"""Test verifying basic package imports and structural skeleton."""

import inspect


def test_package_import() -> None:
    """Verify aegis can be imported cleanly."""
    import aegis

    assert aegis is not None
    assert hasattr(aegis, "__version__")
    assert aegis.__version__ == "0.1.0"


def test_aegis_entrypoint_import() -> None:
    """Verify Aegis main class entrypoint can be imported."""
    from aegis import Aegis

    assert inspect.isclass(Aegis)
    instance = Aegis()
    assert "Aegis" in repr(instance)


def test_subpackages_import() -> None:
    """Verify framework modular subpackages can be imported."""
    import aegis.autonomy
    import aegis.core
    import aegis.evaluation
    import aegis.evidence
    import aegis.incidents
    import aegis.policy
    import aegis.providers
    import aegis.reasoning
    import aegis.reliability
    import aegis.remediation
    import aegis.security

    assert aegis.core is not None
    assert aegis.incidents is not None
    assert aegis.evidence is not None
    assert aegis.reasoning is not None
    assert aegis.reliability is not None
    assert aegis.security is not None
    assert aegis.policy is not None
    assert aegis.autonomy is not None
    assert aegis.remediation is not None
    assert aegis.evaluation is not None
    assert aegis.providers is not None
