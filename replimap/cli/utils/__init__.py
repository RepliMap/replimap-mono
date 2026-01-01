"""CLI utility modules."""

from replimap.cli.utils.aws_session import (
    CREDENTIAL_CACHE_FILE,
    clear_credential_cache,
    get_available_profiles,
    get_aws_session,
    get_cached_credentials,
    get_profile_region,
    save_cached_credentials,
)
from replimap.cli.utils.console import console, get_console, get_logger, logger
from replimap.cli.utils.console_links import get_console_url, get_console_url_from_id
from replimap.cli.utils.helpers import (
    print_graph_stats,
    print_next_steps,
    print_scan_summary,
)
from replimap.cli.utils.options import (
    DryRunOption,
    ForceOption,
    FormatOption,
    OptionalRegionOption,
    OutputDirOption,
    ProfileOption,
    QuietOption,
    RegionOption,
    TagOption,
    VpcOption,
    YesOption,
)

__all__ = [
    # Console
    "console",
    "logger",
    "get_console",
    "get_logger",
    # AWS Session
    "CREDENTIAL_CACHE_FILE",
    "get_aws_session",
    "get_available_profiles",
    "get_profile_region",
    "get_cached_credentials",
    "save_cached_credentials",
    "clear_credential_cache",
    # Options
    "ProfileOption",
    "RegionOption",
    "OptionalRegionOption",
    "OutputDirOption",
    "VpcOption",
    "TagOption",
    "FormatOption",
    "QuietOption",
    "DryRunOption",
    "ForceOption",
    "YesOption",
    # Helpers
    "print_scan_summary",
    "print_graph_stats",
    "print_next_steps",
    # Console Links
    "get_console_url",
    "get_console_url_from_id",
]
