from mmengine.config import read_base
from opencompass.models import Qwen_local
from opencompass.partitioners import NaivePartitioner
from opencompass.runners.local_api import LocalAPIRunner
from opencompass.tasks import OpenICLInferTask

with read_base():
    from ..summarizers.medium import summarizer

    from ..datasets.mmlu.mmlu_gen import mmlu_datasets
    from ..datasets.mbpp.mbpp_gen import mbpp_datasets
    # from ..datasets.humaneval.humaneval_gen import humaneval_datasets
    from ..datasets.bbh.bbh_gen import bbh_datasets


datasets = [

    # *mmlu_datasets,
    # *mbpp_datasets,
    # *humaneval_datasets,
    *bbh_datasets

]

models = [
    dict(
        abbr='qwen-14b-chat',
        type=Qwen_local,
        path='Qwen',
        # requesturl = 'http://acv-gydn.baocloud.cn/acv-service/service/api/6000001561276621/v1/predict/openaiapi/v1/chat/completions',
        requesturl = 'https://acv-gydn.baocloud.cn/acv-service/service/api/6000002067298078/v1/predict/openaiapi/v1/chat/completions',
        temperature = 0.1,
        top_p = 0,
        generation_kwargs={
            'enable_search': False,
        },
        query_per_second=1,
        max_out_len=40960,
        max_seq_len=40960,
        batch_size=1
    ),
]

infer = dict(
    partitioner=dict(type=NaivePartitioner),
    runner=dict(
        type=LocalAPIRunner,
        max_num_workers=2,
        concurrent_users=1,
        task=dict(type=OpenICLInferTask)),
)

work_dir = "outputs/api_qwen/"



