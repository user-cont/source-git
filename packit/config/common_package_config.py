# MIT License
#
# Copyright (c) 2020 Red Hat, Inc.

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Common package config attributes so they can be imported both in PackageConfig and JobConfig
"""
import os
from typing import Dict, List, Optional, Union

from packit.actions import ActionName
from packit.config.notifications import (
    NotificationsConfig,
    PullRequestNotificationsConfig,
)
from packit.config.sync_files_config import SyncFilesConfig
from packit.constants import PROD_DISTGIT_URL
from packit.sync import SyncFilesItem
from packit.utils.repo import get_current_version_command


class CommonPackageConfig:
    """
    We want JobConfig to hold all the attributes from PackageConfig so we don't need to
    pass both PackageConfig and JobConfig to handlers in p-s. We also want people
    to be able to override global PackageConfig attributes per job.

                        CommonPackageConfig
                              /      \
                   PackageConfig   JobConfig
                          //
              contains [JobConfig]
    """

    def __init__(
        self,
        config_file_path: Optional[str] = None,
        specfile_path: Optional[str] = None,
        synced_files: Optional[SyncFilesConfig] = None,
        dist_git_namespace: str = None,
        upstream_project_url: str = None,  # can be URL or path
        upstream_package_name: str = None,
        downstream_project_url: str = None,
        downstream_package_name: str = None,
        dist_git_base_url: str = None,
        create_tarball_command: List[str] = None,
        current_version_command: List[str] = None,
        actions: Dict[ActionName, Union[str, List[str]]] = None,
        upstream_ref: Optional[str] = None,
        allowed_gpg_keys: Optional[List[str]] = None,
        create_pr: bool = True,
        sync_changelog: bool = False,
        spec_source_id: str = "Source0",
        upstream_tag_template: str = "{version}",
        archive_root_dir_template: str = "{upstream_pkg_name}-{version}",
        patch_generation_ignore_paths: List[str] = None,
        notifications: Optional[NotificationsConfig] = None,
        copy_upstream_release_description: bool = False,
    ):
        self.config_file_path: Optional[str] = config_file_path
        self.specfile_path: Optional[str] = specfile_path
        self.synced_files: SyncFilesConfig = synced_files or SyncFilesConfig([])
        self.patch_generation_ignore_paths = patch_generation_ignore_paths or []
        self.dist_git_namespace: str = dist_git_namespace or "rpms"
        self.upstream_project_url: Optional[str] = upstream_project_url
        self.upstream_package_name: Optional[str] = upstream_package_name
        # this is generated by us
        self.downstream_package_name: Optional[str] = downstream_package_name
        self.dist_git_base_url: str = dist_git_base_url or os.getenv(
            "DISTGIT_URL", PROD_DISTGIT_URL
        )
        self._downstream_project_url: str = downstream_project_url
        # path to a local git clone of the dist-git repo; None means to clone in a tmpdir
        self.dist_git_clone_path: Optional[str] = None
        self.actions = actions or {}
        self.upstream_ref: Optional[str] = upstream_ref
        self.allowed_gpg_keys = allowed_gpg_keys
        self.create_pr: bool = create_pr
        self.sync_changelog: bool = sync_changelog
        self.spec_source_id: str = spec_source_id
        self.notifications = notifications or NotificationsConfig(
            pull_request=PullRequestNotificationsConfig()
        )

        # command to generate a tarball from the upstream repo
        # uncommitted changes will not be present in the archive
        self.create_tarball_command: List[str] = create_tarball_command
        # command to get current version of the project
        self.current_version_command: List[
            str
        ] = current_version_command or get_current_version_command(glob_pattern="*")
        # template to create an upstream tag name (upstream may use different tagging scheme)
        self.upstream_tag_template = upstream_tag_template
        self.archive_root_dir_template = archive_root_dir_template
        self.copy_upstream_release_description = copy_upstream_release_description

    def __repr__(self):
        return (
            "CommonPackageConfig("
            f"specfile_path='{self.specfile_path}', "
            f"synced_files='{self.synced_files}', "
            f"dist_git_namespace='{self.dist_git_namespace}', "
            f"upstream_project_url='{self.upstream_project_url}', "
            f"upstream_package_name='{self.upstream_package_name}', "
            f"downstream_project_url='{self.downstream_project_url}', "
            f"downstream_package_name='{self.downstream_package_name}', "
            f"dist_git_base_url='{self.dist_git_base_url}', "
            f"create_tarball_command='{self.create_tarball_command}', "
            f"current_version_command='{self.current_version_command}', "
            f"actions='{self.actions}', "
            f"upstream_ref='{self.upstream_ref}', "
            f"allowed_gpg_keys='{self.allowed_gpg_keys}', "
            f"create_pr='{self.create_pr}', "
            f"synced_files='{self.synced_files}', "
            f"spec_source_id='{self.spec_source_id}', "
            f"upstream_tag_template='{self.upstream_tag_template}', "
            f"patch_generation_ignore_paths='{self.patch_generation_ignore_paths}',"
            f"copy_upstream_release_description='{self.copy_upstream_release_description}')"
        )

    @property
    def downstream_project_url(self) -> str:
        if not self._downstream_project_url:
            self._downstream_project_url = self.dist_git_package_url
        return self._downstream_project_url

    @property
    def dist_git_package_url(self):
        return (
            f"{self.dist_git_base_url}{self.dist_git_namespace}/"
            f"{self.downstream_package_name}.git"
        )

    def get_all_files_to_sync(self):
        """
        Adds the default files (config file, spec file) to synced files when doing propose-update.
        :return: SyncFilesConfig with default files
        """
        files = self.synced_files.files_to_sync

        if self.specfile_path not in (item.src for item in files):
            files.append(
                SyncFilesItem(
                    src=self.specfile_path,
                    dest=f"{self.downstream_package_name}.spec"
                    if self.downstream_package_name
                    else self.specfile_path,
                )
            )

        if self.config_file_path and self.config_file_path not in (
            item.src for item in files
        ):
            # this relative because of glob: "Non-relative patterns are unsupported"
            files.append(
                SyncFilesItem(src=self.config_file_path, dest=self.config_file_path)
            )

        return SyncFilesConfig(files)
