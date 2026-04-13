"""Unit tests for pipeline spec parsing"""

import pytest

from ...pipeline.spec import _parse_raw, PipelineSpec, JobSpec, SpecError


class TestParseRaw:

    def test_valid_spec_returns_pipeline_spec(self):
        raw = {
            "jobs": {
                "build": {
                    "steps": [
                        {"run": "pip install -r requirements.txt"},
                        {"run": "pytest tests/"},
                    ]
                },
                "deploy": {"steps": [{"run": "./deploy.sh"}]},
            }
        }

        result = _parse_raw(raw)

        assert isinstance(result, PipelineSpec)
        assert len(result.jobs) == 2
        assert result.jobs[0] == JobSpec(
            name="build", commands=["pip install -r requirements.txt", "pytest tests/"]
        )
        assert result.jobs[1] == JobSpec(name="deploy", commands=["./deploy.sh"])

    def test_missing_jobs_key_raises(self):
        with pytest.raises(SpecError):
            _parse_raw({})

    def test_non_dict_input_raises(self):
        with pytest.raises(SpecError):
            _parse_raw("not a dict")

    def test_empty_jobs_raises(self):
        with pytest.raises(SpecError):
            _parse_raw({"jobs": {}})

    def test_job_missing_steps_raises(self):
        raw = {"jobs": {"build": {}}}

        with pytest.raises(SpecError, match="steps"):
            _parse_raw(raw)

    def test_empty_steps_raises(self):
        raw = {"jobs": {"build": {"steps": []}}}

        with pytest.raises(SpecError):
            _parse_raw(raw)

    def test_step_missing_run_raises(self):
        raw = {"jobs": {"build": {"steps": [{"not_run": "echo hi"}]}}}

        with pytest.raises(SpecError, match="run"):
            _parse_raw(raw)

    def test_run_as_non_string_raises(self):
        raw = {"jobs": {"build": {"steps": [{"run": 42}]}}}

        with pytest.raises(SpecError, match="string"):
            _parse_raw(raw)

    def test_single_step_job(self):
        raw = {"jobs": {"deploy": {"steps": [{"run": "echo deployed"}]}}}

        result = _parse_raw(raw)

        assert len(result.jobs) == 1
        assert result.jobs[0].commands == ["echo deployed"]
