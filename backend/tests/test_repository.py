from backend.anvaya.repositories.base import Repository
from backend.anvaya.repositories.sqlite import SQLiteRepository
from backend.anvaya.services.auth import seed_users
from werkzeug.security import check_password_hash


def test_sqlite_repository_implements_contract():
    repository = SQLiteRepository.from_url("sqlite:///:memory:")
    assert isinstance(repository, Repository)
    assert repository.health_check() == "ok"
    repository.close()


def test_sqlite_repository_rejects_non_sqlite_url():
    try:
        SQLiteRepository.from_url("postgresql://not-supported")
    except ValueError as error:
        assert "sqlite:///" in str(error)
    else:
        raise AssertionError("Expected unsupported repository URL to fail")


def test_predefined_user_password_rotates_on_reseed():
    repository = SQLiteRepository.from_url("sqlite:///:memory:")
    repository.initialize()
    seed_users(repository, "first-demo-password")
    first_hash = repository.find_active_user_by_username("investigator.demo")["password_hash"]

    seed_users(repository, "rotated-demo-password")
    rotated_hash = repository.find_active_user_by_username("investigator.demo")["password_hash"]

    assert rotated_hash != first_hash
    assert check_password_hash(rotated_hash, "rotated-demo-password")
    repository.close()
