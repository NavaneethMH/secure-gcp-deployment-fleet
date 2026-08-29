from tools.cloud_build_tools import _valid_public_git_url


def test_public_github_url_is_accepted():
    assert _valid_public_git_url(
        "https://github.com/NavaneethMH/secure-gcp-deployment-fleet.git"
    )


def test_non_github_url_is_rejected():
    assert not _valid_public_git_url(
        "https://example.com/user/repo.git"
    )


def test_github_url_without_git_suffix_is_rejected():
    assert not _valid_public_git_url(
        "https://github.com/user/repo"
    )
