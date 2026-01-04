"""
Shell completion support for RepliMap CLI.

Supports:
- Bash
- Zsh
- Fish

Usage:
    # Bash
    eval "$(replimap completion bash)"

    # Zsh
    eval "$(replimap completion zsh)"

    # Fish
    replimap completion fish > ~/.config/fish/completions/replimap.fish
"""

from __future__ import annotations

import configparser
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def get_aws_profiles() -> list[str]:
    """
    Get list of AWS profiles from credentials and config files.

    Returns:
        Sorted list of profile names
    """
    profiles: set[str] = set()

    # Check ~/.aws/credentials
    credentials_file = Path.home() / ".aws" / "credentials"
    if credentials_file.exists():
        profiles.update(_parse_aws_config_profiles(credentials_file))

    # Check ~/.aws/config
    config_file = Path.home() / ".aws" / "config"
    if config_file.exists():
        profiles.update(_parse_aws_config_profiles(config_file, prefix="profile "))

    # Add default if not present
    if not profiles:
        profiles.add("default")

    return sorted(profiles)


def _parse_aws_config_profiles(path: Path, prefix: str = "") -> list[str]:
    """
    Parse profile names from AWS config file.

    Args:
        path: Path to AWS config file
        prefix: Prefix to strip from section names (e.g., "profile " for config file)

    Returns:
        List of profile names
    """
    profiles = []

    try:
        parser = configparser.ConfigParser()
        parser.read(path)

        for section in parser.sections():
            name = section
            if prefix and name.startswith(prefix):
                name = name[len(prefix) :]
            profiles.append(name)

        # Also check for default (no section header in credentials)
        if parser.has_section("default") or (
            path.name == "credentials" and "default" not in profiles
        ):
            if "default" not in profiles:
                profiles.append("default")

    except Exception:
        logger.debug("Failed to parse AWS config file: %s", path)

    return profiles


def get_aws_regions() -> list[str]:
    """
    Get list of AWS regions.

    Returns:
        List of region codes sorted by common usage
    """
    return [
        # US regions (most common)
        "us-east-1",
        "us-east-2",
        "us-west-1",
        "us-west-2",
        # Europe
        "eu-west-1",
        "eu-west-2",
        "eu-west-3",
        "eu-central-1",
        "eu-central-2",
        "eu-north-1",
        "eu-south-1",
        "eu-south-2",
        # Asia Pacific
        "ap-southeast-1",
        "ap-southeast-2",
        "ap-southeast-3",
        "ap-southeast-4",
        "ap-northeast-1",
        "ap-northeast-2",
        "ap-northeast-3",
        "ap-south-1",
        "ap-south-2",
        "ap-east-1",
        # Other
        "sa-east-1",
        "ca-central-1",
        "me-south-1",
        "me-central-1",
        "af-south-1",
        "il-central-1",
    ]


def generate_bash_completion() -> str:
    """Generate Bash completion script."""
    return """# RepliMap Bash Completion
# Add to ~/.bashrc: eval "$(replimap completion bash)"

_replimap_completion() {
    local cur prev words cword
    _init_completion || return

    local commands="scan clone load profiles audit graph drift deps cost remediate validate unused trends transfer cache license upgrade snapshot trust-center dr completion"

    case "${prev}" in
        -p|--profile)
            # Complete AWS profiles
            local profiles=$(grep -hE "^\\[" ~/.aws/credentials ~/.aws/config 2>/dev/null | \\
                           sed 's/\\[profile /[/g' | tr -d '[]' | sort -u)
            COMPREPLY=($(compgen -W "${profiles}" -- "${cur}"))
            return
            ;;
        -r|--region)
            # Complete AWS regions
            local regions="us-east-1 us-east-2 us-west-1 us-west-2 eu-west-1 eu-west-2 eu-west-3 eu-central-1 eu-north-1 ap-southeast-1 ap-southeast-2 ap-northeast-1 ap-northeast-2 ap-south-1 sa-east-1 ca-central-1"
            COMPREPLY=($(compgen -W "${regions}" -- "${cur}"))
            return
            ;;
        -o|--output|--output-dir)
            # Complete directories
            COMPREPLY=($(compgen -d -- "${cur}"))
            return
            ;;
        -f|--format)
            COMPREPLY=($(compgen -W "terraform cloudformation pulumi" -- "${cur}"))
            return
            ;;
        -m|--mode)
            COMPREPLY=($(compgen -W "dry-run generate" -- "${cur}"))
            return
            ;;
        -b|--backend)
            COMPREPLY=($(compgen -W "local s3" -- "${cur}"))
            return
            ;;
        completion)
            COMPREPLY=($(compgen -W "bash zsh fish install" -- "${cur}"))
            return
            ;;
    esac

    case "${cword}" in
        1)
            COMPREPLY=($(compgen -W "${commands}" -- "${cur}"))
            ;;
        *)
            case "${words[1]}" in
                scan|clone|graph|deps|audit|drift|cost)
                    COMPREPLY=($(compgen -W "-p --profile -r --region -o --output -v --verbose -h --help" -- "${cur}"))
                    ;;
                cache)
                    COMPREPLY=($(compgen -W "list show clear" -- "${cur}"))
                    ;;
                license)
                    COMPREPLY=($(compgen -W "status activate deactivate" -- "${cur}"))
                    ;;
                completion)
                    COMPREPLY=($(compgen -W "bash zsh fish install" -- "${cur}"))
                    ;;
                *)
                    COMPREPLY=($(compgen -W "-h --help" -- "${cur}"))
                    ;;
            esac
            ;;
    esac
}

complete -F _replimap_completion replimap
"""


def generate_zsh_completion() -> str:
    """Generate Zsh completion script."""
    return """#compdef replimap
# RepliMap Zsh Completion
# Add to ~/.zshrc: eval "$(replimap completion zsh)"

_replimap() {
    local state

    _arguments -C \\
        '1: :->command' \\
        '*: :->args'

    case $state in
        command)
            local commands=(
                'scan:Scan AWS account for resources'
                'clone:Clone infrastructure to Terraform'
                'load:Load cached scan results'
                'profiles:List AWS profiles'
                'graph:Visualize dependency graph'
                'drift:Detect configuration drift'
                'audit:Run security audit'
                'cost:Estimate infrastructure costs'
                'deps:Show resource dependencies'
                'remediate:Generate remediation code'
                'validate:Validate resources'
                'unused:Find unused resources'
                'trends:Show usage trends'
                'transfer:Transfer resources'
                'cache:Manage scan cache'
                'license:Manage license'
                'upgrade:Upgrade RepliMap'
                'snapshot:Manage snapshots'
                'trust-center:Security trust center'
                'dr:Disaster recovery'
                'completion:Generate shell completion'
            )
            _describe 'command' commands
            ;;
        args)
            case $words[2] in
                scan|clone|graph|deps|audit|drift|cost)
                    _arguments \\
                        '-p[AWS profile]:profile:->profiles' \\
                        '--profile[AWS profile]:profile:->profiles' \\
                        '-r[AWS region]:region:->regions' \\
                        '--region[AWS region]:region:->regions' \\
                        '-o[Output directory]:directory:_files -/' \\
                        '--output[Output directory]:directory:_files -/' \\
                        '--output-dir[Output directory]:directory:_files -/' \\
                        '-v[Verbose output]' \\
                        '--verbose[Verbose output]' \\
                        '-h[Show help]' \\
                        '--help[Show help]'
                    ;;
                clone)
                    _arguments \\
                        '-p[AWS profile]:profile:->profiles' \\
                        '--profile[AWS profile]:profile:->profiles' \\
                        '-r[AWS region]:region:->regions' \\
                        '--region[AWS region]:region:->regions' \\
                        '-o[Output directory]:directory:_files -/' \\
                        '--output-dir[Output directory]:directory:_files -/' \\
                        '-f[Output format]:format:(terraform cloudformation pulumi)' \\
                        '--format[Output format]:format:(terraform cloudformation pulumi)' \\
                        '-m[Mode]:mode:(dry-run generate)' \\
                        '--mode[Mode]:mode:(dry-run generate)' \\
                        '-b[Backend type]:backend:(local s3)' \\
                        '--backend[Backend type]:backend:(local s3)' \\
                        '--backend-bucket[S3 bucket for state]:bucket:' \\
                        '--backend-key[S3 key for state file]:key:' \\
                        '--backend-region[S3 bucket region]:region:->regions' \\
                        '--backend-dynamodb[DynamoDB table for locking]:table:' \\
                        '--backend-bootstrap[Generate bootstrap Terraform]' \\
                        '-h[Show help]' \\
                        '--help[Show help]'
                    ;;
                cache)
                    _arguments \\
                        '1:subcommand:(list show clear)'
                    ;;
                license)
                    _arguments \\
                        '1:subcommand:(status activate deactivate)'
                    ;;
                completion)
                    _arguments \\
                        '1:shell:(bash zsh fish install)'
                    ;;
            esac

            case $state in
                profiles)
                    local profiles
                    profiles=(${(f)"$(grep -hE '^\\[' ~/.aws/credentials ~/.aws/config 2>/dev/null | \\
                              sed 's/\\[profile /[/g' | tr -d '[]' | sort -u)"})
                    _describe 'AWS profile' profiles
                    ;;
                regions)
                    local regions=(
                        'us-east-1:N. Virginia'
                        'us-east-2:Ohio'
                        'us-west-1:N. California'
                        'us-west-2:Oregon'
                        'eu-west-1:Ireland'
                        'eu-west-2:London'
                        'eu-west-3:Paris'
                        'eu-central-1:Frankfurt'
                        'eu-north-1:Stockholm'
                        'ap-southeast-1:Singapore'
                        'ap-southeast-2:Sydney'
                        'ap-northeast-1:Tokyo'
                        'ap-northeast-2:Seoul'
                        'ap-south-1:Mumbai'
                        'sa-east-1:Sao Paulo'
                        'ca-central-1:Canada'
                    )
                    _describe 'AWS region' regions
                    ;;
            esac
            ;;
    esac
}

_replimap "$@"
"""


def generate_fish_completion() -> str:
    """Generate Fish completion script."""
    return """# RepliMap Fish Completion
# Save to: ~/.config/fish/completions/replimap.fish

# Disable file completion by default
complete -c replimap -f

# Commands
complete -c replimap -n "__fish_use_subcommand" -a "scan" -d "Scan AWS account for resources"
complete -c replimap -n "__fish_use_subcommand" -a "clone" -d "Clone infrastructure to Terraform"
complete -c replimap -n "__fish_use_subcommand" -a "load" -d "Load cached scan results"
complete -c replimap -n "__fish_use_subcommand" -a "profiles" -d "List AWS profiles"
complete -c replimap -n "__fish_use_subcommand" -a "graph" -d "Visualize dependency graph"
complete -c replimap -n "__fish_use_subcommand" -a "drift" -d "Detect configuration drift"
complete -c replimap -n "__fish_use_subcommand" -a "audit" -d "Run security audit"
complete -c replimap -n "__fish_use_subcommand" -a "cost" -d "Estimate infrastructure costs"
complete -c replimap -n "__fish_use_subcommand" -a "deps" -d "Show resource dependencies"
complete -c replimap -n "__fish_use_subcommand" -a "remediate" -d "Generate remediation code"
complete -c replimap -n "__fish_use_subcommand" -a "validate" -d "Validate resources"
complete -c replimap -n "__fish_use_subcommand" -a "unused" -d "Find unused resources"
complete -c replimap -n "__fish_use_subcommand" -a "cache" -d "Manage scan cache"
complete -c replimap -n "__fish_use_subcommand" -a "license" -d "Manage license"
complete -c replimap -n "__fish_use_subcommand" -a "completion" -d "Generate shell completion"

# Profile completion function
function __fish_replimap_profiles
    grep -hE "^\\[" ~/.aws/credentials ~/.aws/config 2>/dev/null | \\
        sed 's/\\[profile /[/g' | tr -d '[]' | sort -u
end

# Region list
set -l regions us-east-1 us-east-2 us-west-1 us-west-2 eu-west-1 eu-west-2 eu-west-3 eu-central-1 eu-north-1 ap-southeast-1 ap-southeast-2 ap-northeast-1 ap-northeast-2 ap-south-1 sa-east-1 ca-central-1

# Common options for main commands
complete -c replimap -n "__fish_seen_subcommand_from scan clone graph deps audit drift cost" -s p -l profile -d "AWS profile" -xa "(__fish_replimap_profiles)"
complete -c replimap -n "__fish_seen_subcommand_from scan clone graph deps audit drift cost" -s r -l region -d "AWS region" -xa "$regions"
complete -c replimap -n "__fish_seen_subcommand_from scan clone graph" -s o -l output -l output-dir -d "Output directory" -r

# Clone-specific options
complete -c replimap -n "__fish_seen_subcommand_from clone" -s f -l format -d "Output format" -xa "terraform cloudformation pulumi"
complete -c replimap -n "__fish_seen_subcommand_from clone" -s m -l mode -d "Mode" -xa "dry-run generate"
complete -c replimap -n "__fish_seen_subcommand_from clone" -s b -l backend -d "Backend type" -xa "local s3"
complete -c replimap -n "__fish_seen_subcommand_from clone" -l backend-bucket -d "S3 bucket for state"
complete -c replimap -n "__fish_seen_subcommand_from clone" -l backend-key -d "S3 key for state file"
complete -c replimap -n "__fish_seen_subcommand_from clone" -l backend-region -d "S3 bucket region" -xa "$regions"
complete -c replimap -n "__fish_seen_subcommand_from clone" -l backend-dynamodb -d "DynamoDB table for locking"
complete -c replimap -n "__fish_seen_subcommand_from clone" -l backend-bootstrap -d "Generate bootstrap Terraform"

# Cache subcommands
complete -c replimap -n "__fish_seen_subcommand_from cache" -a "list" -d "List cached scans"
complete -c replimap -n "__fish_seen_subcommand_from cache" -a "show" -d "Show cache details"
complete -c replimap -n "__fish_seen_subcommand_from cache" -a "clear" -d "Clear cache"

# License subcommands
complete -c replimap -n "__fish_seen_subcommand_from license" -a "status" -d "Show license status"
complete -c replimap -n "__fish_seen_subcommand_from license" -a "activate" -d "Activate license"
complete -c replimap -n "__fish_seen_subcommand_from license" -a "deactivate" -d "Deactivate license"

# Completion subcommands
complete -c replimap -n "__fish_seen_subcommand_from completion" -a "bash" -d "Generate Bash completion"
complete -c replimap -n "__fish_seen_subcommand_from completion" -a "zsh" -d "Generate Zsh completion"
complete -c replimap -n "__fish_seen_subcommand_from completion" -a "fish" -d "Generate Fish completion"
complete -c replimap -n "__fish_seen_subcommand_from completion" -a "install" -d "Show installation instructions"

# Global options
complete -c replimap -s h -l help -d "Show help"
complete -c replimap -s V -l version -d "Show version"
complete -c replimap -s v -l verbose -d "Verbose output"
complete -c replimap -s q -l quiet -d "Quiet mode"
"""


def get_install_instructions(shell: str) -> str:
    """
    Get installation instructions for shell completion.

    Args:
        shell: Shell type (bash, zsh, fish)

    Returns:
        Installation instructions
    """
    if shell == "bash":
        return """# Bash Completion Installation

# Option 1: Add to ~/.bashrc (recommended)
echo 'eval "$(replimap completion bash)"' >> ~/.bashrc
source ~/.bashrc

# Option 2: Save to system completions directory
replimap completion bash | sudo tee /etc/bash_completion.d/replimap > /dev/null

# Option 3: Save to user directory (if using bash-completion)
mkdir -p ~/.local/share/bash-completion/completions
replimap completion bash > ~/.local/share/bash-completion/completions/replimap
"""

    elif shell == "zsh":
        return """# Zsh Completion Installation

# Option 1: Add to ~/.zshrc (recommended)
echo 'eval "$(replimap completion zsh)"' >> ~/.zshrc
source ~/.zshrc

# Option 2: Save to completions directory
mkdir -p ~/.zfunc
replimap completion zsh > ~/.zfunc/_replimap

# Then add to ~/.zshrc (before compinit):
# fpath=(~/.zfunc $fpath)
# autoload -Uz compinit && compinit
"""

    elif shell == "fish":
        return """# Fish Completion Installation

# Save to Fish completions directory
mkdir -p ~/.config/fish/completions
replimap completion fish > ~/.config/fish/completions/replimap.fish

# Completions will be available in new Fish sessions
# To use immediately, run:
source ~/.config/fish/completions/replimap.fish
"""

    return f"Unknown shell: {shell}"
