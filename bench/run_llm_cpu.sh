#!/bin/bash
# Untrained LLMs on a CPU-only machine, in short runs with thermal pauses. Ollama must be running in a container named "ollama".
# Each request waits until the CPU package is below COOL C; 3 min gap between models; everything stops at ABORT C.
# Usage (root, Intel RAPL needed for energy): KP_HOME=/path/to/kalparso-release bash bench/run_llm_cpu.sh
# Optional: SPECS="model:n ..." (models and number of timed entries), COOL, KP_THINK=low (gpt-oss)
cd "${KP_HOME:?set KP_HOME to the repository root}"
OUT=results/stress; mkdir -p $OUT; DATA=data/human/human_test.jsonl; COOL=${COOL:-85}; ABORT=${ABORT:-98}
D="docker run --rm --pid host --network host --mount type=bind,source=/sys/devices/virtual/powercap/intel-rapl/intel-rapl:0,target=/rapl0,readonly --mount type=bind,source=/sys/devices/virtual/thermal,target=/thermal,readonly -v $PWD:/w -w /w -e KP_THINK python:3.12-slim python bench/stress.py"
temp() { for z in /sys/class/thermal/thermal_zone*; do [ "$(cat $z/type)" = x86_pkg_temp ] && echo $(( $(cat $z/temp) / 1000 )); done; }
unload() { curl -s localhost:11434/api/generate -d "{\"model\":\"$1\",\"keep_alive\":0}" >/dev/null; }
blob() { docker exec ollama ollama show "$1" --modelfile | awk '/^FROM \/root/{print $2}' | xargs basename; }
# watchdog: stop everything if the package ever reaches ABORT
( while sleep 2; do t=$(temp); if [ "${t:-0}" -ge $ABORT ]; then echo "ABORT $t C $(date)"; docker ps -q --filter ancestor=python:3.12-slim | xargs -r docker kill; docker exec ollama sh -c 'pkill -f "ollama runner"; pkill llama-server'; touch $OUT/ABORTED; exit; fi; done ) &
WD=$!
for spec in ${SPECS:-qwen3.5:0.8b:30 qwen3.5:4b:30 llama3.1:8b:20 qwen3:8b:20 gemma3:12b:15 gemma4:26b:15 qwen3:30b-a3b:15 gemma3:27b:10 gpt-oss:20b:10}; do
  n=${spec##*:}; m=${spec%:*}; t=llmcpu_$(echo $m | tr ':/' '__')
  [ -e $OUT/ABORTED ] && break
  [ -s $OUT/$t.json ] && continue
  echo "== $m n=$n $(date +%T) $(temp)C"
  $D ollama $m $DATA results/stress/$t.json --proc "$(blob $m)" --single $n --conc "" --spike 2 --cool $COOL 2>&1 | grep -E "^(single|spike)|Error|error"
  unload $m; echo "   done $(date +%T) $(temp)C"; sleep 180
done
kill $WD; echo "LLM CPU DONE $(date)"
