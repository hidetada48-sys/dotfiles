"""
Gemini 画像生成スクリプト（汎用版）
どのリポジトリからでも呼び出せる standalone スクリプト

使い方：
  python3 generate_image.py "プロンプト（英語）" [--output 保存先.png] [--model モデルID]

環境変数：
  GOOGLE_API_KEY  Google AI Studio の APIキー（必須）
"""

import os
import sys
import argparse
from datetime import datetime
from pathlib import Path

from google import genai
from google.genai import types

# デフォルトモデル（Nano Banana Pro）
DEFAULT_MODEL = "gemini-3-pro-image-preview"


def main():
    parser = argparse.ArgumentParser(description="Gemini 画像生成")
    parser.add_argument("prompt", help="画像生成プロンプト（英語）")
    parser.add_argument("--output", "-o", help="保存先ファイルパス（省略時は ./generated_YYYYMMDD_HHMMSS.png）")
    parser.add_argument("--model", "-m", default=DEFAULT_MODEL, help=f"使用モデル（デフォルト: {DEFAULT_MODEL}）")
    args = parser.parse_args()

    # APIキーの確認
    api_key = os.environ.get("GOOGLE_API_KEY", "")
    if not api_key:
        print("❌ GOOGLE_API_KEY が設定されていません")
        print("  → ~/.bashrc に export GOOGLE_API_KEY=xxx を追加してください")
        sys.exit(1)

    # 保存先の決定
    if args.output:
        output_path = Path(args.output)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path(f"generated_{timestamp}.png")

    print(f"モデル     │ {args.model}")
    print(f"プロンプト │ {args.prompt[:60]}{'...' if len(args.prompt) > 60 else ''}")
    print(f"保存先     │ {output_path}")
    print("生成中...")

    # Gemini クライアントの初期化と画像生成
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=args.model,
        contents=args.prompt,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE", "TEXT"],
        )
    )

    # レスポンスから画像データを取り出して保存
    image_bytes = None
    for part in response.candidates[0].content.parts:
        if part.inline_data is not None:
            image_bytes = part.inline_data.data
            break

    if image_bytes is None:
        print("❌ 画像データが返ってきませんでした")
        sys.exit(1)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(image_bytes)

    print(f"✅ 保存完了: {output_path.resolve()}")


if __name__ == "__main__":
    main()
