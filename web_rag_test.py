from langchain_community.tools import DuckDuckGoSearchRun
from langchain_ollama import OllamaLLM

# ① Web検索（無料・APIキー不要）
search = DuckDuckGoSearchRun()

query = "ESP32 PWM 複数ピン 同一チャンネル"
web_result = search.run(query)

print("=== Web Search Result (truncated) ===")
print(web_result[:500])
print("====================================")

# ② Ollama LLM（★接続先を明示指定）
llm = OllamaLLM(
    model="codellama:7b-instruct",
    base_url="http://127.0.0.1:11434",  # ← 重要
    temperature=0.2
)

# ③ LLMに渡すプロンプト
prompt = f"""
以下はWeb検索結果です。

{web_result}

これを参考に、ESP32でPWMを複数ピンに同時出力する
最小構成のArduinoコードを生成してください。
"""

# ④ 実行
response = llm.invoke(prompt)

print("\n=== LLM Response ===")
print(response)
