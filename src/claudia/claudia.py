import os
import os.path
import subprocess

import click
import inquirer
from inquirer.themes import GreenPassion

class SingletonClass(object):
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(SingletonClass, cls).__new__(cls)
        return cls.instance


singleton = SingletonClass()
singleton.PROJECT_ROOT_DIR = os.path.dirname(__file__)


def set_to_project_root_wd():
    os.chdir(singleton.PROJECT_ROOT_DIR)


@click.group()
@click.version_option(message=f'%(prog)s version %(version)s')
def main():
    """Claudia says hi! Please choose a command to perform an action. A command can have multiple sub-commands and options. Use '--help' option for more information."""


@main.command()
def demo():
    """Launch claudia in demo mode"""
    try:
        clear_screen()
        launch_main_menu()
    except Exception as e:
        pass


def launch_main_menu():
    questions = [
        inquirer.List(
            "main_menu",
            message="Welcome to Claudia Demo! Please use ↑ ↓ and ↵ keys to choose an option. Current Selection",
            choices=[
                "Custom XRPL Networks",
                "Settings",
                "Exit"
            ],
        ),
    ]

    selection_text = inquirer.prompt(questions, theme=GreenPassion())['main_menu']

    if selection_text == "Custom XRPL Networks":
        clear_screen()
        launch_custom_rippled_networks_menu()
    elif selection_text == "Settings":
        clear_screen()
        launch_settings_menu()
    elif selection_text == 'Exit':
        print("Thank you for using Claudia demo. Bye!")
        return


def launch_custom_rippled_networks_menu():
    relaunch_wizard = True
    questions = [
        inquirer.List(
            "rippled_task_menu",
            message="Here you can find a list of rippled related tasks. Please use ↑ ↓ and ↵ keys to choose an option. Current Selection",
            choices=[
                "Build rippled from local code",
                "Install rippled",
                "Start local-mainnet",
                "Stop local-mainnet",
                "Check local-mainnet status",
                "Back to main menu"
            ],
        ),
    ]

    selection_text = inquirer.prompt(questions, theme=GreenPassion())['rippled_task_menu']
    if selection_text == "Build rippled from local code":
        relaunch_wizard = False
        repo_path = get_valid_repo_path()
        if repo_path == "" or repo_path.replace("'", "").replace('"', '').lower() == 'back':
            relaunch_wizard = True
        else:
            clear_screen()
            print("\nINFO: In order to '{}', run: 'claudia rippled build --repo <absolute_path_to_local_repo>'".format(
                selection_text))
            print("You have opted to execute '{}'. Starting now...\n".format(selection_text))
            launch_command_rippled_build(repo_path)
    elif selection_text == 'Install rippled':
        relaunch_wizard = False
        clear_screen()
        rippled_branch = get_rippled_branch()
        if rippled_branch == "" or rippled_branch.replace("'", "").replace('"', '').lower() == 'back':
            relaunch_wizard = True
        else:
            clear_screen()
            print("\nINFO: In order to '{}', run: 'claudia rippled install --rippled_branch <branch_name>'".format(
                selection_text))
            print("You have opted to execute '{}'. Starting now...\n".format(selection_text))
            launch_command_rippled_install(rippled_branch.lower())
    elif selection_text == 'Start local-mainnet':
        relaunch_wizard = False
        clear_screen()
        print("\nINFO: In order to '{}', run: 'claudia local-mainnet start'".format(selection_text))
        print("You have opted to execute '{}'. Starting now...\n".format(selection_text))
        launch_command_network_start()
    elif selection_text == 'Check local-mainnet status':
        relaunch_wizard = False
        clear_screen()
        print("\nINFO: In order to '{}', run: 'claudia local-mainnet status'".format(selection_text))
        print("You have opted to execute '{}'. Starting now...\n".format(selection_text))
        launch_command_network_status()
    elif selection_text == 'Stop local-mainnet':
        relaunch_wizard = False
        clear_screen()
        print("\nINFO: In order to '{}', run: 'claudia local-mainnet stop'".format(selection_text))
        print("You have opted to execute '{}'. Starting now...\n".format(selection_text))
        launch_command_network_stop()
    elif selection_text == 'Back to main menu':
        clear_screen()
        launch_main_menu()
        return

    if relaunch_wizard:
        clear_screen()
        launch_custom_rippled_networks_menu()
    else:
        if get_confirmation("Would you like to continue with the demo?"):
            clear_screen()
            launch_custom_rippled_networks_menu()
        else:
            print("Thank you for using Claudia demo. Bye!")
            return


def launch_settings_menu():
    relaunch_wizard = True
    questions = [
        inquirer.List(
            "misc_task_menu",
            message="Here you can find a list of all the settings. Please use ↑ ↓ and ↵ keys to choose an option. Current Selection",
            choices=[
                "Set install mode as build",
                "Set install mode as install",
                "Enable a rippled feature",
                "Disable a rippled feature",
                "Clean up the host and free resources",
                "List system requirements (prerequisites)",
                "Print already built/installed rippled version",
                "Back to main menu"
            ],
        ),
    ]

    selection_text = inquirer.prompt(questions, theme=GreenPassion())['misc_task_menu']
    if selection_text == 'List system requirements (prerequisites)':
        relaunch_wizard = False
        clear_screen()
        print("\nINFO: In order to '{}', run: 'claudia list system-requirements'".format(selection_text))
        print("You have opted to execute '{}'. Starting now...\n".format(selection_text))
        launch_command_system_requirements()
    elif selection_text == 'Set install mode as build':
        relaunch_wizard = False
        clear_screen()
        print("\nINFO: In order to '{}', run: 'claudia set-install-mode build'".format(selection_text))
        print("You have opted to execute '{}'. Starting now...\n".format(selection_text))
        launch_command_set_install_mode_to_build()
    elif selection_text == 'Set install mode as install':
        relaunch_wizard = False
        clear_screen()
        print("\nINFO: In order to '{}', run: 'claudia set-install-mode install'".format(selection_text))
        print("You have opted to execute '{}'. Starting now...\n".format(selection_text))
        launch_command_set_install_mode_to_install()
    elif selection_text == 'Enable a rippled feature':
        relaunch_wizard = False
        clear_screen()
        print("\nINFO: In order to '{}', run: 'claudia enable-feature --feature <feature_name>'".format(selection_text))
        print("You have opted to execute '{}'. Starting now...\n".format(selection_text))
        feature_name = get_feature_name()
        if feature_name == "" or feature_name.replace("'", "").replace('"', '').lower() == 'back':
            relaunch_wizard = True
        else:
            launch_command_enable_feature(feature_name)
    elif selection_text == 'Disable a rippled feature':
        relaunch_wizard = False
        clear_screen()
        print("\nINFO: In order to '{}', run: 'claudia disable-feature --feature <feature_name>'".format(
            selection_text
        ))
        print("You have opted to execute '{}'. Starting now...\n".format(selection_text))
        feature_name = get_feature_name()
        if feature_name == "" or feature_name.replace("'", "").replace('"', '').lower() == 'back':
            relaunch_wizard = True
        else:
            launch_command_disable_feature(feature_name)
    elif selection_text == 'Clean up the host and free resources':
        relaunch_wizard = False
        clear_screen()
        print("\nINFO: In order to '{}', run: 'claudia clean'".format(selection_text))
        print("You have opted to execute '{}'. Starting now...\n".format(selection_text))
        launch_command_clean()
    elif selection_text == 'Print already built/installed rippled version'.format(selection_text):
        relaunch_wizard = False
        clear_screen()
        print("\nINFO: In order to '{}', run: 'claudia rippled version'".format(selection_text))
        print("You have opted to execute '{}'. Starting now...\n".format(selection_text))
        launch_command_rippled_version()
    elif selection_text == 'Back to main menu':
        clear_screen()
        launch_main_menu()
        return

    if relaunch_wizard:
        clear_screen()
        launch_settings_menu()
    else:
        if get_confirmation("Would you like to continue with the demo?"):
            clear_screen()
            launch_settings_menu()
        else:
            print("Thank you for using Claudia demo. Bye!")
            return


def get_valid_repo_path():
    input_path = [
        inquirer.Text('repo path',
                      message="Please enter the absolute path to the rippled repo. Type 'back' or simply press ↵ (return) key to skip and go back to main menu.")
    ]
    full_repo_path = inquirer.prompt(input_path, theme=GreenPassion())['repo path']
    if full_repo_path == "" or full_repo_path == "back":
        pass
    else:
        if not os.path.isabs(full_repo_path) or not os.path.exists(full_repo_path):
            print(
                "The rippled repository path '{}' is not correct. Please provide correct absolute path!".format(
                    full_repo_path))
            return get_valid_repo_path()

    return full_repo_path


def get_rippled_branch():
    rippled_branch = inquirer.prompt(
        [inquirer.List("rippled_branch", message="Please choose rippled branch. Current Selection",
                       choices=["master", "develop", "release"], default="master")],
        theme=GreenPassion()
    )['rippled_branch']
    return rippled_branch


def get_feature_name():
    feature_name = [
        inquirer.Text('feature_name',
                      message="Please enter the feature name. Type 'back' or simply press ↵ (return) key to skip and go back to main menu.")
    ]
    return inquirer.prompt(feature_name, theme=GreenPassion())['feature_name']


def get_confirmation(confirmation_message):
    q = [inquirer.List("confirmation", message=confirmation_message, choices=["Yes", "No"], default="No")]
    answer = inquirer.prompt(q, theme=GreenPassion())['confirmation']
    if answer == 'Yes':
        return_value = True
    else:
        return_value = False
    return return_value


def clear_screen():
    if os.name == 'posix':
        os.system('clear')
    elif os.name == 'nt':
        os.system('cls')


@main.group()
def rippled():
    """Build or install rippled"""


@main.group()
def local_mainnet():
    """Setup rippled Network"""


@main.group()
def set_install_mode():
    """Setup Install Mode"""


@main.command()
def clean():
    """Clean up the host and free resources"""
    launch_command_clean()


def launch_command_clean(ask_confirmation=True):
    if ask_confirmation:
        print("WARNING!! Running this command will wipe out everything built by Claudia. This action cannot be undone.")
        input("Press enter to continue or ctrl+c to cancel...")

    command = get_launch_command_clean()
    return subprocess.call(command, shell=True)


def get_launch_command_clean():
    set_to_project_root_wd()
    return "sh network_setup/setup.sh --clean"


@main.command()
@click.option('--feature', required=True, help="The rippled feature name")
def enable_feature(feature):
    """Enable rippled feature"""
    launch_command_enable_feature(feature)


def launch_command_enable_feature(feature):
    command = get_launch_command_enable_feature(feature)
    return subprocess.call(command, shell=True)


def get_launch_command_enable_feature(feature):
    set_to_project_root_wd()
    return "sh network_setup/setup.sh --enableFeature {}".format(feature)


@main.command()
@click.option('--feature', required=True, help="The rippled feature name")
def disable_feature(feature):
    """Disable rippled feature"""
    launch_command_disable_feature(feature)


def launch_command_disable_feature(feature):
    command = get_launch_command_disable_feature(feature)
    return subprocess.call(command, shell=True)


def get_launch_command_disable_feature(feature):
    set_to_project_root_wd()
    return "sh network_setup/setup.sh --disableFeature {}".format(feature)


@main.group()
def list():
    """List supported options"""


@set_install_mode.command()
def build():
    """Set install mode to build"""
    launch_command_set_install_mode_to_build()


def launch_command_set_install_mode_to_build():
    command = get_launch_command_set_install_mode_to_build()
    return subprocess.call(command, shell=True)


def get_launch_command_set_install_mode_to_build():
    set_to_project_root_wd()
    return "sh network_setup/setup.sh --setInstallMode build"


@set_install_mode.command()
def install():
    """Set install mode to install"""
    launch_command_set_install_mode_to_install()


def launch_command_set_install_mode_to_install():
    command = get_launch_command_set_install_mode_to_install()
    return subprocess.call(command, shell=True)


def get_launch_command_set_install_mode_to_install():
    set_to_project_root_wd()
    return "sh network_setup/setup.sh --setInstallMode install"


@list.command()
def system_requirements():
    """List all system requirements before continuing further with claudia"""
    launch_command_system_requirements()


def launch_command_system_requirements():
    click.echo(get_launch_command_system_requirements_message())


def get_launch_command_system_requirements_message():
    message = """
    1. Common requirements:
        - Python3
        - pip
        - docker
    2. Pull down a fresh copy of rippled code base from https://github.com/XRPLF/rippled
    3. Optional: Following depedencies are only required if you intend to run Javascript tests:
        - node
        - npm
    
        More detailed information can be found under the 'General prerequisite' section here: https://pypi.org/project/claudia
    """
    return message


@rippled.command()
@click.option('--repo', required=True, help="The path to a local rippled repo")
def build(repo):
    """Build rippled from source"""
    launch_command_rippled_build(repo)


def launch_command_rippled_build(repo):
    if not os.path.isabs(repo) or not os.path.exists(repo):
        click.echo(
            " - ERROR: The rippled repository path '{}' is not correct. Please provide correct absolute path!".format(repo))
        return
    command = get_launch_command_rippled_build(repo)
    return subprocess.call(command, shell=True)


def get_launch_command_rippled_build(repo):
    set_to_project_root_wd()
    return "sh network_setup/setup.sh --rippledBuild --repo {}".format(repo)


@rippled.command()
def version():
    """View rippled version info"""
    launch_command_rippled_version()


def launch_command_rippled_version():
    command = get_launch_command_rippled_version()
    return subprocess.call(command, shell=True)


def get_launch_command_rippled_version():
    set_to_project_root_wd()
    return "sh network_setup/setup.sh --rippledVersion"


@rippled.command()
@click.option('--rippled_branch', default='master', help="Source branch for rippled binaries")
def install(rippled_branch):
    """Install rippled packages"""
    launch_command_rippled_install(rippled_branch)


def launch_command_rippled_install(rippled_branch):
    if rippled_branch not in ['master', 'develop', 'release']:
        print(f"The rippled branch '{rippled_branch}' is not correct. Allowed values are master, develop and release (case-sensitive).")
        return
    command = get_launch_command_rippled_install(rippled_branch)
    return subprocess.call(command, shell=True)


def get_launch_command_rippled_install(rippled_branch):
    set_to_project_root_wd()
    return f"sh network_setup/setup.sh --rippledInstall --rippledBranch {rippled_branch}"


@local_mainnet.command()
def start():
    """Start a new rippled network"""
    launch_command_network_start()


def launch_command_network_start():
    command = get_launch_command_network_start()
    return subprocess.call(command, shell=True)


def get_launch_command_network_start():
    set_to_project_root_wd()
    return "sh ./network_setup/setup.sh --networkStart"


@local_mainnet.command()
def stop():
    """Stop rippled network"""
    launch_command_network_stop()


def launch_command_network_stop():
    command = get_launch_command_network_stop()
    return subprocess.call(command, shell=True)


def get_launch_command_network_stop():
    set_to_project_root_wd()
    return "sh ./network_setup/setup.sh --networkStop"


@local_mainnet.command()
def status():
    """rippled network status"""
    launch_command_network_status()


def launch_command_network_status():
    command = get_launch_command_network_status()
    return subprocess.call(command, shell=True)


def get_launch_command_network_status():
    set_to_project_root_wd()
    return "sh ./network_setup/setup.sh --networkStatus"


def get_explorer_url(network):
    url = ""
    if network == 'testnet':
        url = "https://testnet.xrpl.org"
    elif network == 'devnet':
        url = "https://devnet.xrpl.org"
    else:
        url = "https://custom.xrpl.org/localhost:6001"

    return url


if __name__ == '__main__':
    main(context, obj={})
