from mmengine.config import read_base
from opencompass.models import PanGu
from opencompass.partitioners import NaivePartitioner
from opencompass.runners.local_api import LocalAPIRunner
from opencompass.tasks import OpenICLInferTask

with read_base():
    from ..summarizers.medium import summarizer
    from ..datasets.mmlu.mmlu_gen import mmlu_datasets
    from ..datasets.ceval.ceval_gen import ceval_datasets
    # from ..datasets.gsm8k.gsm8k_gen import gsm8k_datasets
    # from ..datasets.bbh.bbh_gen import bbh_datasets
    # from ..datasets.cmmlu.cmmlu_gen import cmmlu_datasets
    from ..datasets.hellaswag.hellaswag_gen import hellaswag_datasets

datasets = [
    # *ceval_datasets,
    # *gsm8k_datasets
    # *bbh_datasets
    # *cmmlu_datasets
    *mmlu_datasets,
    # *hellaswag_datasets,
]

models = [
dict(
        abbr='pangu',
        type=PanGu,
        path='pangu',
        # access_key="HE13BMXWJ3MXKF47BJTG",
        # secret_key="uWMU2s0Ac7nXcP6YxXHj0Kdv35tO4dJ23CY0kn4m",
        # url = "/v1/infers/822873d8-0998-460b-944d-b53b9405bd81/v1/da6cf2e2d3634de8a610b02cf3e0f211/deployments/3dcfee36-e338-4a01-b273-0679d4b057bb/chat/completions",
        url = 'http://10.83.8.91:8080/v1/da6/deployments/3dc/chat/completions',
        # url of token sever, used for generate token, like "https://xxxxxx.myhuaweicloud.com/v3/auth/tokens",
        # token_url = "https://iam.cn-southwest-2.myhuaweicloud.com/v3/auth/tokens",
        # scope-project-name, used for generate token
        # project_name = "cn-southwest-2",
        query_per_second=1,
        max_out_len=9192,
        max_seq_len=9192,
        batch_size=1),
]

infer = dict(
    partitioner=dict(type=NaivePartitioner),
    runner=dict(
        type=LocalAPIRunner,
        max_num_workers=1,
        concurrent_users=1,
        task=dict(type=OpenICLInferTask)),
)

work_dir = "outputs/api_pangu/"

