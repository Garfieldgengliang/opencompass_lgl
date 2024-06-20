from mmengine.config import read_base

with read_base():
    from .datasets.siqa.siqa_gen import siqa_datasets
    from .datasets.winograd.winograd_ppl import winograd_datasets
    from .models.opt.hf_opt_125m import opt125m
    from .models.opt.hf_opt_350m import opt350m
    from .models.qwen.hf_qwen1_5_14b_chat import models


datasets = [*siqa_datasets, *winograd_datasets]
models = [opt125m, opt350m]
