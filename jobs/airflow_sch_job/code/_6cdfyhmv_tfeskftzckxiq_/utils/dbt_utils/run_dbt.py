import shlex
import subprocess
import zipfile
from typing import Optional
import json
import logging
import sys
import traceback
import base64
import os
import re
import tempfile
from dbt.cli.main import dbtRunner, dbtRunnerResult
import shutil
import time
from keyring.testing.util import random_string


# setup logging
logging.basicConfig()
LOG = logging.getLogger('shell')


## for pm-fabs
def get_secret(secret_id: str) -> Optional[str]:
    from google.cloud import secretmanager
    project_id = os.getenv('PROPHECY_PROJECT_ID')
    LOG.info(f"Trying to fetch secret - {secret_id} for prophecy project id {project_id}")

    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(name=name)
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        LOG.error(f"ERROR: Failed to fetch secret for {secret_id}", e)
        raise e

def create_temp_file():
    filename = f"tempfile_{int(time.time())}_{random_string(6)}"
    file_path = os.path.join("/tmp", filename)
    file = open(file_path, "w")
    file.close()
    return file_path


def set_git_keypass(git_file, git_secret: str):
    if git_secret and len(git_secret) > 0:
        git_secret_val = get_secret(git_secret)
        if git_secret_val and len(git_secret_val) > 0:
            with open(git_file, "w") as f:
                f.write(f'#!/bin/sh\necho {git_secret_val}\n')
                f.flush()
            os.chmod(git_file, 0o700)
            os.environ["GIT_ASKPASS"] = git_file


def make_dbt_profiles_dir(root_dir, secret: str):
    if secret and len(secret) > 0:
        secret_val = get_secret(f"airflow-connections-{secret}")
        if secret_val and len(secret_val) > 0:
            with open(f"{root_dir}/profiles.yml", "w") as f:
                f.write(base64.urlsafe_b64decode(secret_val).decode('utf-8'))
                f.flush()


## dbt commands
runner = dbtRunner()


def execute_dbt_cmd(command):
    try:
        response = runner.invoke(command.split()[1:])
        if response.success:
            LOG.info(f"command %s and result %s", command, response.result)
            return response.result
        else:
            raise response.exception

    except Exception as e:
        LOG.error(f"Error running dbt command {command}", str(e))
        raise e


## extract dependency of same package only.
def key(name: str, kind: str):
    return f"{name}:::{kind}"


def extract_node_name_from_dbt_dependency(dbt_dep_str: str):
    return dbt_dep_str.split(".")[-1]


class SqlEntity:
    def __init__(self, line: dict):
        self.line = line

    def unique_key(self):
        return key(self.line['name'], self.line['resource_type'])

    def package_name(self):
        return self.line['package_name']

    def resource_type(self):
        return self.line['resource_type']

    def node_name(self):
        return self.line['name']

    def depends_on(self):
        if 'depends_on' in self.line and 'nodes' in self.line['depends_on']:
            return self.line['depends_on']['nodes']
        else:
            return []


def get_dependency_path(entities: dict, entity_key: str, package_name: str) -> list:
    if entity_key not in entities:
        return []
    else:
        nodes_depends_on = entities[entity_key].depends_on()
        dependencies = []
        for node_unique_id in nodes_depends_on:
            if package_name in node_unique_id:
                node_name = extract_node_name_from_dbt_dependency(node_unique_id)
                if node_unique_id.startswith("seed"):
                    dependencies = get_dependency_path(entities, key(node_name, "seed"), package_name) + dependencies
                elif node_unique_id.startswith("model"):
                    dependencies = get_dependency_path(entities, key(node_name, "model"), package_name) + dependencies
                elif node_unique_id.startswith("snapshot"):
                    dependencies = get_dependency_path(entities, key(node_name, "snapshot"),
                                                       package_name) + dependencies
            # do nothing.
        return dependencies + [entities[entity_key]]


def prune_duplicates(dependency_path: list) -> list:
    output_list = []
    seen_keys = set()

    for node in dependency_path:
        if node.unique_key() not in seen_keys:
            seen_keys.add(node.unique_key())
            output_list.append(node)

    return output_list


def dbt_command_executor(folder_path: str, suffix: str):
    cmd = f"dbt ls --project-dir {folder_path} {suffix} --output=json"
    LOG.info(f"Running command {cmd}")
    response = execute_dbt_cmd(cmd)
    LOG.info("Response from dbt cmd %s", response)
    entities = {}

    for line in response:
        if line:
            entity = SqlEntity(json.loads(line))
            entities[entity.unique_key()] = entity

    return entities


def dbt_dependency_extractor(folder_path: str, entity_kind: str, entity_name: str, suffix: str):
    entities = dbt_command_executor(folder_path, suffix)
    entity_key = key(entity_name, entity_kind)
    return prune_duplicates(get_dependency_path(entities, entity_key, entities[entity_key].package_name()))


def dbt_find_child_for_node(project_folder: str, entityName: str, dbt_props_cmd: str):
    entities = dbt_command_executor(project_folder, dbt_props_cmd)
    children = set()
    for node in entities.values():
        for n in node.depends_on():
            if n.startwith("model") and entityName in n:
                children.add(node)
            elif n.startwith("snapshot") and entityName in n:
                children.add(node)
        ## --NA--
    return list(children)


def get_parents(run_parents: bool, project_folder: str, entityKind: str, entityName: str, dbt_props_cmd: str,
                exclude_nodes=[]):
    parents = []
    if run_parents:
        nodes = dbt_dependency_extractor(project_folder, entityKind, entityName, dbt_props_cmd)
        LOG.info(f"run_parents {run_parents} nodes {nodes}")
        for node in nodes:
            if node.resource_type() == "model":
                parents.append(f"dbt run -m {node.node_name()} {dbt_props_cmd}")
            elif node.resource_type() == "snapshot":
                parents.append(f"dbt snapshot -s {node.node_name()} {dbt_props_cmd}")
        LOG.info(f"all parents {parents[:-1]}")
    all_parents = parents[:-1]  # removing the last element as it is the entity itself.
    parents_after_removing_exclude = [parent for parent in all_parents if
                                      all(node not in parent for node in exclude_nodes)]
    LOG.info(f"Parents after removing exclude {parents_after_removing_exclude} before exclude {all_parents}")
    return parents_after_removing_exclude


def get_children(run_children: bool, project_folder: str, entityName: str, dbt_props_cmd: str,
                 exclude_nodes=[]):
    children = []

    if run_children:
        nodes = dbt_find_child_for_node(project_folder, entityName, dbt_props_cmd)
        LOG.info(f"run children {run_children} nodes {nodes}")
        for node in nodes:
            if node.resource_type() == "model":
                children.append(f"dbt run -m {node.node_name()} {dbt_props_cmd}")
            elif node.resource_type() == "snapshot":
                children.append(f"dbt snapshot -s {node.node_name()} {dbt_props_cmd}")

    children_after_removing_exclude = [child for child in children if all(node not in child for node in exclude_nodes)]
    LOG.info(f"Children after removing exclude {children_after_removing_exclude} before exclude {children}")
    return children_after_removing_exclude


def remove_files_and_folders(path):
    try:
        if os.path.isfile(path):
            os.remove(path)
            LOG.info(f"Removed file: {path}")
        elif os.path.isdir(path):
            shutil.rmtree(path)
            LOG.info(f"Removed folder and its contents: {path}")
        else:
            LOG.info(f"Path not found: {path}")
    except Exception as e:
        LOG.error(f"Failed to remove {path}: {e}")


########################################################  runner command ##############################################

def run_command(props: str, project_folder: str, dep: bool, seeds: bool, run_mode: str,
                entity_kind: str, entity_name: str, run_parents: bool, run_children: bool,
                run_test: bool, cmd_list=[],
                select: Optional[str] = "", exclude=[]):
    props = f" {props} --project-dir {project_folder}"
    select_suffix = f" -s {select}" if select else ""
    if dep:
        cmd_list = cmd_list + [f"dbt deps {props}"]
    if seeds:
        cmd_list = cmd_list + [f"dbt seed {props}"]
    if run_mode == "project":
        cmd_list = cmd_list + [f"dbt run {props} {select_suffix}"]
    else:
        cmd_list = cmd_list + get_parents(run_parents, project_folder, entity_kind, entity_name, props,
                                          exclude)
        LOG.info(cmd_list)
        if entity_kind == "model":
            cmd_list = cmd_list + [f"dbt run --model {entity_name} {select_suffix} {props}"]
        else:
            cmd_list = cmd_list + [f"dbt snapshot -s {entity_name} {select_suffix} {props}"]
        cmd_list = cmd_list + get_children(run_children, project_folder, entity_name, props,
                                           exclude)
    if run_test:
        cmd_list = cmd_list + [f"dbt test {props}"]

    LOG.info(f"Running command in one time run {cmd_list}")

    for cmd in cmd_list:
        LOG.info(f"Command: {cmd}")
        if cmd.startswith("dbt "):
            try:
                response = execute_dbt_cmd(cmd)
                LOG.info(f"Response from dbt cmd {response}")
            except Exception as e:
                LOG.error(f"Command failed with exit code", e)
                raise Exception(f"Command failed with exit code %s", e)
        else:
            ## for cmd like git clone.
            try:
                ## don't use log for result output
                ## it doesn't get serialized and print other crap.

                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=False)
                if result.returncode != 0:
                    raise Exception(f"Command failed with exit code {result.returncode} and error {result.stderr}")

            except subprocess.CalledProcessError as e:
                LOG.error(f"Command failed with exit code", e)
                raise Exception(f"Command failed with exit code {e.returncode} and error {e.stderr}")



########################################################  CMD invokers ##############################################
def invoke_dbt_runner(run_mode, entity_kind, entity_name, run_deps,
                      run_seeds, run_props, run_parents, run_children, run_tests,
                      select, exclude, git_ssh_url, git_entity, git_entity_value, git_sub_path,
                      git_token_secret: str, dbt_profile_secret: str, envs: dict, **kwargs):
    for key, value in envs.items():
        os.environ[key] = value

    file_path = os.path.dirname(os.path.abspath(__file__))
    temp_folder = tempfile.mkdtemp(dir="/tmp")
    tmp_file = create_temp_file()
    try:

        file_path_as_list = file_path.split("/")
        zip_index = next((i for i, part in enumerate(file_path_as_list) if part.endswith('.zip')), None)

        def extract_folder_from_zip(zip_file_path, folder_name):
            with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                for file in zip_ref.namelist():
                    if file.startswith(folder_name):
                        zip_ref.extract(file, temp_folder)

        zip_path = "/".join(file_path_as_list[:(zip_index + 1)])
        extract_folder_from_zip(zip_path, "project")
        project_folder = f"{temp_folder}/project"
        LOG.info(f"project_folder: {project_folder} + flag:{(os.path.isdir(project_folder))} zip_path:{zip_path}")

        cmd_list = []
        if not (os.path.isdir(project_folder)):
            project_folder = temp_folder
            git_cmd = "git clone "
            if git_entity == "branch":
                git_cmd = git_cmd + "{} --branch {} --single-branch {}".format(
                    git_ssh_url, git_entity_value, project_folder
                )
            elif git_entity == "tag":
                git_cmd = git_cmd + "--depth 1 {} --branch {} {}".format(
                    git_ssh_url, git_entity_value, project_folder
                )
            else:
                git_cmd = git_cmd + "{} {} && git checkout {}".format(
                    git_ssh_url, project_folder, git_entity_value
                )

            cmd_list = [git_cmd]

        set_git_keypass(tmp_file, git_token_secret)

        LOG.info(f"Prophecy managed update on path {project_folder}")
        make_dbt_profiles_dir(project_folder, dbt_profile_secret)

        run_props = run_props + f" --profiles-dir {project_folder}"
        run_command(props=run_props,
                    project_folder=project_folder,
                    dep=run_deps,
                    seeds=run_seeds,
                    run_mode=run_mode,
                    entity_kind=entity_kind,
                    entity_name=entity_name,
                    run_parents=run_parents,
                    run_children=run_children,
                    run_test=run_tests,
                    cmd_list=cmd_list,
                    select=select,
                    exclude=exclude)
    finally:
        LOG.info(f"Cleaning up temp folder {temp_folder} and temp file {tmp_file}")
        remove_files_and_folders(temp_folder)
        remove_files_and_folders(tmp_file)
        