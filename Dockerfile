# 프로젝트 이미지 = lab/isaaclab + uv sync (system site-packages 위). 코드는 파이프라인이 git 으로 가져온다.
ARG BASE=lab/isaaclab:2.1.1-isaacsim4.5.0-20260913
FROM ${BASE}
WORKDIR /workspace
COPY pyproject.toml uv.lock .python-version ./
RUN --mount=type=secret,id=gh_token,required=false \
    if [ -s /run/secrets/gh_token ]; then git config --global url."https://x-access-token:$(cat /run/secrets/gh_token)@github.com/".insteadOf "https://github.com/"; fi \
    && uv venv --system-site-packages --python /isaac-sim/kit/python/bin/python3 .venv \
    && uv sync --frozen --no-install-project --no-dev \
    && rm -f /root/.gitconfig
# 경로 우선순위는 /isaac-sim/python.sh 와 같다: Isaac 번들 > venv (templates/isaac-lab 과 동일한 이유).
ENV PATH=/workspace/.venv/bin:$PATH VIRTUAL_ENV=/workspace/.venv
