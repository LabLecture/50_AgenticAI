intel@intel:~/Downloads$ export LLM_ENDPOINT_PORT=8008
intel@intel:~/Downloads$ export host_ip=192.168.100.87
intel@intel:~/Downloads$ export HF-TOKEN=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
intel@intel:~/Downloads$ export LLM_ENDPOINT="http://${host_ip}:${LLM_ENDPOINT_PORT}"
intel@intel:~/Downloads$ export LLM_MODEL_ID="deepcogito/cogito-v1-preview-llama-8B"

intel@intel:~/Downloads$ sudo usermod -aG render,docker $USER
intel@intel:~/Downloads$ newgrp render

# 1. huggingface-cli 를 통한 모델 다운로드 전 ACCESS_TOKEN 설정
(venv) intel@intel:~/Documents/chatbot/vllm$ git config --global credential.helper store
(venv) intel@intel:~/Documents/chatbot/vllm$ export HF_TOKEN="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"
(venv) intel@intel:~/Documents/chatbot/vllm$ huggingface-cli login
(venv) intel@intel:~/Documents/chatbot/vllm$ huggingface-cli whoami

# 2. cogito-8B 모델 사용 - try 1
(venv) intel@intel:~/Documents/chatbot/vllm$ sudo mkdir cogito-8B
(venv) intel@intel:~/Documents/chatbot/vllm$ sudo chown intel.intel cogito-8B
(venv) intel@intel:~/Documents/chatbot/vllm$ cd cogito-8B/
(venv) intel@intel:~/Documents/chatbot/vllm/cogito-8B$ huggingface-cli download deepcogito/cogito-v1-preview-llama-8B --local-dir . --local-dir-use-symlinks False

## https://hub.docker.com/r/opea/vllm-arc
## 1. 호스트(PC)에 모델이 저장된 실제 경로
export LOCAL_MODEL_PATH="/home/intel/Documents/chatbot/vllm/cogito-8B"

## 2. 컨테이너 내부에서 모델을 인식할 경로 (보통 /models 로 지정)
export CONTAINER_MODEL_PATH=/models

## 3. 사용할 포트, 호스트 IP, 허깅페이스 토큰 등 설정
export LLM_PORT=8008
export HOST_IP="0.0.0.0" # 외부에서 접속하려면 0.0.0.0 으로 설정
export HF_TOKEN="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" # 토크나이저 다운로드 등에 필요할 수 있음

docker run -d --rm \
    --name="vllm-cogito-8B" \
    -p ${LLM_PORT}:8000 \
    --ipc=host \
    --device=/dev/dri \
    -v ${LOCAL_MODEL_PATH}:${CONTAINER_MODEL_PATH} \
    -e HUGGING_FACE_HUB_TOKEN=${HF_TOKEN} \
    -e ZES_ENABLE_SYSMAN=1 opea/vllm-arc \
    --model ${CONTAINER_MODEL_PATH} \
    --host ${HOST_IP} \
    --port 8000

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

docker run -d --rm \
    --name="vllm-cogito-8B" \
    -p ${LLM_PORT}:8000 \
    --ipc=host \
    --device=/dev/dri \
    -v ${LOCAL_MODEL_PATH}:${CONTAINER_MODEL_PATH} \
    -e HUGGING_FACE_HUB_TOKEN=${HF_TOKEN} \
    -e ZES_ENABLE_SYSMAN=1 \
    -e MODEL_PATH=${CONTAINER_MODEL_PATH} \
    -e HOST=${HOST_IP} \
    -e PORT=8000 \
    opea/vllm-arc

docker run --rm opea/vllm-arc --help
docker inspect opea/vllm-arc
docker run -it --rm opea/vllm-arc /bin/bash

docker logs vllm-cogito-8B  

docker run \
    --name="vllm-cogito-8B-debug" \
    -p ${LLM_PORT}:8000 \
    --ipc=host \
    --device=/dev/dri \
    -v ${LOCAL_MODEL_PATH}:${CONTAINER_MODEL_PATH} \
    -e HUGGING_FACE_HUB_TOKEN=${HF_TOKEN} \
    -e ZES_ENABLE_SYSMAN=1 \
    opea/vllm-arc \
    python3 -m vllm.entrypoints.openai.api_server \
    --model ${CONTAINER_MODEL_PATH} \
    --host ${HOST_IP} \
    --port 8000
  

    ERROR 07-19 10:29:37 engine.py:366]     self._init_worker()
    ERROR 07-19 10:29:37 engine.py:366]   File "/usr/local/lib/python3.10/dist-packages/vllm/executor/openvino_executor.py", line 50, in _init_worker
    ERROR 07-19 10:29:37 engine.py:366]     self.driver_worker.load_model()
    ERROR 07-19 10:29:37 engine.py:366]   File "/usr/local/lib/python3.10/dist-packages/vllm/worker/openvino_worker.py", line 253, in load_model
    ERROR 07-19 10:29:37 engine.py:366]     self.model_runner.load_model()
    ERROR 07-19 10:29:37 engine.py:366]   File "/usr/local/lib/python3.10/dist-packages/vllm/worker/openvino_model_runner.py", line 81, in load_model
    ERROR 07-19 10:29:37 engine.py:366]     self.model = get_model(model_config=self.model_config,
    ERROR 07-19 10:29:37 engine.py:366]   File "/usr/local/lib/python3.10/dist-packages/vllm/model_executor/model_loader/openvino.py", line 202, in get_model
    ERROR 07-19 10:29:37 engine.py:366]     return OpenVINOCausalLM(ov_core, model_config, device_config,
    ERROR 07-19 10:29:37 engine.py:366]   File "/usr/local/lib/python3.10/dist-packages/vllm/model_executor/model_loader/openvino.py", line 128, in __init__
    ERROR 07-19 10:29:37 engine.py:366]     pt_model = OVModelForCausalLM.from_pretrained(
    ERROR 07-19 10:29:37 engine.py:366]   File "/usr/local/lib/python3.10/dist-packages/optimum/intel/openvino/modeling_base.py", line 504, in from_pretrained
    ERROR 07-19 10:29:37 engine.py:366]     return super().from_pretrained(
    ERROR 07-19 10:29:37 engine.py:366]   File "/usr/local/lib/python3.10/dist-packages/optimum/modeling_base.py", line 408, in from_pretrained
    ERROR 07-19 10:29:37 engine.py:366]     return from_pretrained_method(
    ERROR 07-19 10:29:37 engine.py:366]   File "/usr/local/lib/python3.10/dist-packages/optimum/modeling_base.py", line 314, in _export
    ERROR 07-19 10:29:37 engine.py:366]     raise NotImplementedError(
    ERROR 07-19 10:29:37 engine.py:366] NotImplementedError: Overwrite this method in subclass to define how to load your model from vanilla hugging face model



docker run -d --rm \
    --name="vllm-cogito-8B" \
    -p ${LLM_PORT}:8000 \
    --ipc=host \
    --device=/dev/dri \
    -v ${LOCAL_MODEL_PATH}:${CONTAINER_MODEL_PATH} \
    -e HUGGING_FACE_HUB_TOKEN=${HF_TOKEN} \
    -e ZES_ENABLE_SYSMAN=1 \
    opea/vllm-arc \
    python3 -m vllm.entrypoints.openai.api_server \
    --model ${CONTAINER_MODEL_PATH} \
    --host ${HOST_IP} \
    --port 8000 \
    --trust-remote-code \
    --enforce-eager

추가된 옵션 설명:
--trust-remote-code: cogito-8B 모델처럼 허깅페이스에 공식 등록되지 않은 커스텀 코드가 포함된 모델을 로드할 때 필요한 옵션.
--enforce-eager: (핵심) vLLM이 최적화된 백엔드 대신 기본 실행 엔진(eager mode)을 사용하도록 강제합니다. 이 옵션은 특정 모델과의 호환성 문제를 해결하는 데 매우 효과적  

ERROR 07-19 17:15:08 engine.py:366]     self.engine = LLMEngine(*args, **kwargs)
ERROR 07-19 17:15:08 engine.py:366]   File "/usr/local/lib/python3.10/dist-packages/vllm/engine/llm_engine.py", line 273, in __init__
ERROR 07-19 17:15:08 engine.py:366]     self.model_executor = executor_class(vllm_config=vllm_config, )
ERROR 07-19 17:15:08 engine.py:366]   File "/usr/local/lib/python3.10/dist-packages/vllm/executor/executor_base.py", line 36, in __init__
ERROR 07-19 17:15:08 engine.py:366]     self._init_executor()
ERROR 07-19 17:15:08 engine.py:366]   File "/usr/local/lib/python3.10/dist-packages/vllm/executor/openvino_executor.py", line 31, in _init_executor
ERROR 07-19 17:15:08 engine.py:366]     self._init_worker()
ERROR 07-19 17:15:08 engine.py:366]   File "/usr/local/lib/python3.10/dist-packages/vllm/executor/openvino_executor.py", line 50, in _init_worker
ERROR 07-19 17:15:08 engine.py:366]     self.driver_worker.load_model()
ERROR 07-19 17:15:08 engine.py:366]   File "/usr/local/lib/python3.10/dist-packages/vllm/worker/openvino_worker.py", line 253, in load_model
ERROR 07-19 17:15:08 engine.py:366]     self.model_runner.load_model()
ERROR 07-19 17:15:08 engine.py:366]   File "/usr/local/lib/python3.10/dist-packages/vllm/worker/openvino_model_runner.py", line 81, in load_model
ERROR 07-19 17:15:08 engine.py:366]     self.model = get_model(model_config=self.model_config,
ERROR 07-19 17:15:08 engine.py:366]   File "/usr/local/lib/python3.10/dist-packages/vllm/model_executor/model_loader/openvino.py", line 202, in get_model
ERROR 07-19 17:15:08 engine.py:366]     return OpenVINOCausalLM(ov_core, model_config, device_config,
ERROR 07-19 17:15:08 engine.py:366]   File "/usr/local/lib/python3.10/dist-packages/vllm/model_executor/model_loader/openvino.py", line 128, in __init__
ERROR 07-19 17:15:08 engine.py:366]     pt_model = OVModelForCausalLM.from_pretrained(
ERROR 07-19 17:15:08 engine.py:366]   File "/usr/local/lib/python3.10/dist-packages/optimum/intel/openvino/modeling_base.py", line 504, in from_pretrained
ERROR 07-19 17:15:08 engine.py:366]     return super().from_pretrained(
ERROR 07-19 17:15:08 engine.py:366]   File "/usr/local/lib/python3.10/dist-packages/optimum/modeling_base.py", line 408, in from_pretrained
ERROR 07-19 17:15:08 engine.py:366]     return from_pretrained_method(
ERROR 07-19 17:15:08 engine.py:366]   File "/usr/local/lib/python3.10/dist-packages/optimum/modeling_base.py", line 314, in _export
ERROR 07-19 17:15:08 engine.py:366]     raise NotImplementedError(
ERROR 07-19 17:15:08 engine.py:366] NotImplementedError: Overwrite this method in subclass to define how to load your model from vanilla hugging face model
Process SpawnProcess-2:


OpenVINO에서 잘 지원되는 표준 모델을 사용하는 것이 좋습니다. mistralai/Mistral-7B-Instruct-v0.2 모델로 테스트

(venv) intel@intel:~/Documents/chatbot/vllm$ sudo mkdir Mistral-7B-Instruct-v0.2
(venv) intel@intel:~/Documents/chatbot/vllm$ sudo chown intel.intel Mistral-7B-Instruct-v0.2/
(venv) intel@intel:~/Documents/chatbot/vllm$ cd Mistral-7B-Instruct-v0.2/
(venv) intel@intel:~/Documents/chatbot/vllm/Mistral-7B-Instruct-v0.2$ huggingface-cli download mistralai/Mistral-7B-Instruct-v0.2 --local-dir . --local-dir-use-symlinks False
- huggingface attain Token Access
Access to model mistralai/Mistral-7B-Instruct-v0.2 is restricted and you are not in the authorized list. Visit https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.2 to ask for access. 

ping huggingface.co
curl https://huggingface.co

# 3. Mistral-7B-Instruct-v0.2 다운로드가 잘 안됨. ㅠㅠ - try 2 ...
  File "/home/intel/Documents/chatbot/chatbot_origin/venv/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1648, in _raise_on_head_call_error
    raise LocalEntryNotFoundError(
huggingface_hub.errors.LocalEntryNotFoundError: An error happened while trying to locate the file on the Hub and we cannot find the requested files in the local cache. Please check your connection and try again or make sure your Internet connection is on.


# 4. 회사 서버 try
export HF_TOKEN="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"

tako@4gpu:/data2/vllm/models/Mistral-7B-Instruct-v0.2$ huggingface-cli download mistralai/Mistral-7B-Instruct-v0.2 --local-dir . --local-dir-use-symlinks False
usage: huggingface-cli <command> [<args>]
huggingface-cli: error: invalid choice: 'download' (choose from 'env', 'login', 'whoami', 'logout', 'repo', 'lfs-enable-largefiles', 'lfs-multipart-upload', 'scan-cache', 'delete-cache')

# 5. 회사 서버 - gemma-7b-it  
(/data2/conda_env/vllm) tako@4gpu:/data2/vllm/models$ sudo mkdir gemma-7b-it
(/data2/conda_env/vllm) tako@4gpu:/data2/vllm/models$ sudo chown tako.tako gemma-7b-it/
(/data2/conda_env/vllm) tako@4gpu:/data2/vllm/models$ cd gemma-7b-it/
(/data2/conda_env/vllm) tako@4gpu:/data2/vllm/models/gemma-7b-it$ huggingface-cli download google/gemma-7b-it --local-dir . --local-dir-use-symlinks False
    raise LocalEntryNotFoundError(
huggingface_hub.errors.LocalEntryNotFoundError: An error happened while trying to locate the file on the Hub and we cannot find the requested files in the local cache. Please check your connection and try again or make sure your Internet connection is on.
