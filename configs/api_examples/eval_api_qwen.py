from mmengine.config import read_base
from opencompass.models import Qwen
from opencompass.partitioners import NaivePartitioner
from opencompass.runners.local_api import LocalAPIRunner
from opencompass.tasks import OpenICLInferTask

with read_base():
    from ..summarizers.medium import summarizer
    from ..datasets.ceval.ceval_gen import ceval_datasets
    # from ..datasets.mmlu.mmlu_gen import mmlu_datasets
    # from ..datasets.mbpp.mbpp_gen import mbpp_datasets
    from ..datasets.bbh.bbh_gen import bbh_datasets
datasets = [
    # *ceval_datasets,
    # *mmlu_datasets,
    *bbh_datasets
    # *mbpp_datasets,
]

models = [
    dict(
        abbr='qwen1.5-14b-chat',
        type=Qwen,
        path='qwen1.5-14b-chat',
        # key='sk-3d3b31396f2f4576a78c901e0fcafc03',  # please give you key
        # key = 'sk-12b6451a9fb44e259fa2443b34dfee64',
        key = 'sk-353ee4f0906c4e0ab81990060a427471',
        generation_kwargs={
            'enable_search': False,
        },
        query_per_second=1,
        max_out_len=9192,
        max_seq_len=9192,
        batch_size=4
    ),
]

infer = dict(
    partitioner=dict(type=NaivePartitioner),
    runner=dict(
        type=LocalAPIRunner,
        max_num_workers=1,
        concurrent_users=1,
        task=dict(type=OpenICLInferTask)),
)

work_dir = "outputs/api_qwen/"
