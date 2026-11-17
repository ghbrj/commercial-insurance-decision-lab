Shared schemas across tasks: attribute codebook schema, decision enum
(STP_ACCEPT | REFER | DECLINE), reason-code schema (id, guide_section,
description), manifest schema (run id, task, guide_version, corpus_version,
runner, model, temperature/seed, prompt_hash, timestamps).
Define these YAML schemas here FIRST — every task spec validates against them.
