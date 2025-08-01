from buildserver.builder.builder import Builder
import pytest


builder = Builder()

def test_build():
    
    build_repo = "../hello"
    assert builder.build(build_repo) == True

    bad_build_repo = "../thisdoesntexist"
    with pytest.raises(OSError):
        builder.build(bad_build_repo)