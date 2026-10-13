# Atlas CLI

Entry point: `python scripts/atlas.py <command>`

## run
Full plan → fit → queue → rhythm → readiness → QC → render → post-QC
```bash
python scripts/atlas.py run \
  --narration examples/samples/product_explainer_narration.txt \
  --duration 28 \
  --dna examples/styles/product_snappy_v1.json \
  --profile examples/profiles/product.json \
  --assets product_hook_card,product_script_card \
  --edit-id demo --out renders/demo.mp4 --qc --post-qc
```

## loop
Review notes → revision → re-render cycle (see `atlas.py loop -h`).

## review
```bash
python scripts/atlas.py review --edit path/edit_spec.json --video path/out.mp4 --out review.html
```

## notes
```bash
python scripts/atlas.py notes --edit edit_spec.json --notes notes.txt --out revision.json
```

## queue
```bash
python scripts/asset_queue.py init --fit fit_report.json --out acquisition_queue.json
```

## fit
```bash
python scripts/atlas.py fit --edit edit_spec.json --out fit_report.json
```

## ready
```bash
python scripts/atlas.py ready --fit fit_report.json --queue acquisition_queue.json --edit edit_spec.json
```

## qc-render
```bash
python scripts/atlas.py qc-render --video out.mp4 --edit edit_spec.json --out post_qc.json
```

## qc-provenance
```bash
python scripts/atlas.py qc-provenance --edit edit_spec.json --profile examples/profiles/investigative.json --fail-closed
```

## qc-rhythm
```bash
python scripts/atlas.py qc-rhythm --edit edit_spec.json --profile examples/profiles/product.json --out rhythm.json
```

Also: `python scripts/atlas_pipeline.py` for the orchestrated path with the same flags.
