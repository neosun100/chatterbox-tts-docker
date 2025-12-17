#!/bin/bash
# Chatterbox TTS API 测试脚本

PORT=${1:-7866}
BASE_URL="http://localhost:${PORT}"

echo "Testing Chatterbox TTS API at ${BASE_URL}"
echo "=========================================="

# 1. 健康检查
echo -e "\n1. Health Check"
curl -s "${BASE_URL}/health" | python3 -m json.tool

# 2. GPU 状态
echo -e "\n2. GPU Status"
curl -s "${BASE_URL}/gpu/status" | python3 -m json.tool

# 3. TTS 生成（无参考音频）
echo -e "\n3. TTS Generation (default voice)"
curl -s -X POST "${BASE_URL}/api/tts" \
  -F "text=Hello, this is a test of the Chatterbox TTS system. [chuckle] Pretty cool, right?" \
  -F "temperature=0.8" \
  -o test_output.wav

if [ -f test_output.wav ]; then
    echo "✅ Audio saved to test_output.wav"
    file test_output.wav
else
    echo "❌ Failed to generate audio"
fi

# 4. GPU 状态（生成后）
echo -e "\n4. GPU Status (after generation)"
curl -s "${BASE_URL}/gpu/status" | python3 -m json.tool

# 5. 手动卸载
echo -e "\n5. Offload GPU"
curl -s -X POST "${BASE_URL}/gpu/offload" | python3 -m json.tool

# 6. 验证卸载
echo -e "\n6. GPU Status (after offload)"
curl -s "${BASE_URL}/gpu/status" | python3 -m json.tool

# 7. Swagger 文档
echo -e "\n7. Swagger Docs"
curl -s -o /dev/null -w "Swagger UI: %{http_code}\n" "${BASE_URL}/apidocs/"

# 8. Web UI
echo -e "\n8. Web UI"
curl -s -o /dev/null -w "Web UI: %{http_code}\n" "${BASE_URL}/"

echo -e "\n=========================================="
echo "Test completed!"
echo ""
echo "Access points:"
echo "  Web UI:     ${BASE_URL}/"
echo "  API Docs:   ${BASE_URL}/apidocs/"
echo "  Health:     ${BASE_URL}/health"
