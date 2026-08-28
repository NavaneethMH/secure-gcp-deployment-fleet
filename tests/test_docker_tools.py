from pathlib import Path

from tools.docker_tools import generate_dockerfile


def test_streamlit_generation_requires_real_entrypoint(tmp_path):
    (tmp_path / "requirements.txt").write_text(
        "streamlit\n",
        encoding="utf-8",
    )

    result = generate_dockerfile(
        project_path=str(tmp_path),
        framework="streamlit",
        runtime="python:3.11",
        startup_command="streamlit run app.py",
        port=8080,
    )

    assert result.startswith("ERROR:")
    assert "No supported Streamlit entrypoint found" in result
    assert not (tmp_path / "Dockerfile").exists()


def test_streamlit_generation_uses_existing_app(tmp_path):
    (tmp_path / "requirements.txt").write_text(
        "streamlit\n",
        encoding="utf-8",
    )

    (tmp_path / "app.py").write_text(
        "import streamlit as st\nst.write('hello')\n",
        encoding="utf-8",
    )

    result = generate_dockerfile(
        project_path=str(tmp_path),
        framework="streamlit",
        runtime="python:3.11",
        startup_command="streamlit run app.py",
        port=8080,
    )

    assert result.startswith("SUCCESS:")
    assert "Entrypoint: app.py" in result

    dockerfile = (tmp_path / "Dockerfile").read_text(
        encoding="utf-8",
    )

    assert 'CMD ["streamlit", "run", "app.py"' in dockerfile
    assert "http.server" not in dockerfile


def test_streamlit_generation_selects_main_when_app_missing(tmp_path):
    (tmp_path / "requirements.txt").write_text(
        "streamlit\n",
        encoding="utf-8",
    )

    (tmp_path / "main.py").write_text(
        "import streamlit as st\nst.write('hello')\n",
        encoding="utf-8",
    )

    result = generate_dockerfile(
        project_path=str(tmp_path),
        framework="streamlit",
        runtime="python:3.11",
        startup_command="streamlit run main.py",
        port=8080,
    )

    assert result.startswith("SUCCESS:")
    assert "Entrypoint: main.py" in result

    dockerfile = (tmp_path / "Dockerfile").read_text(
        encoding="utf-8",
    )

    assert 'CMD ["streamlit", "run", "main.py"' in dockerfile
    assert "http.server" not in dockerfile
