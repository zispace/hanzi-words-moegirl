import argparse
import json
import logging
from pathlib import Path
import random
import shutil
import time

import httpx
from fake_useragent import UserAgent

API_URL = "https://zh.moegirl.org.cn/api.php"
PARAMS = {
    "action": "query",
    "list": "allpages",
    "aplimit": "max",  # 每次最多 500 条 (非bot)
    "format": "json",
}


def fetch_all_titles(save_name: str, limit: int = -1, restart: bool = False):
    httpx_logger = logging.getLogger("httpx")
    httpx_logger.setLevel(logging.WARNING)

    save_dir = Path(save_name)
    if restart:
        if save_dir.exists():
            logging.warning("清理目录")
            shutil.rmtree(save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)

    ua = UserAgent()
    headers = {"User-Agent": ua.random}
    params = {k: v for k, v in PARAMS.items()}

    files = sorted(Path(save_dir).glob("*.json"))
    i = 0
    if files:
        old_file = files[-1]
        with open(old_file, encoding="utf-8") as f:
            logging.info(f"读取文件 = {old_file}")
            data = json.load(f)
            if "continue" in data:
                params.update(data["continue"])
            i = int(old_file.stem) + 1

    logging.info(f"start page = {i}")
    data_count = 0
    if limit > 0:
        limit = i + limit - 1
    while (limit <= 0) or (i <= limit):
        r = httpx.get(API_URL, params=params, timeout=30, headers=headers)
        r.raise_for_status()
        if "<script>" in r.text:
            logging.warning("403 forbid")
            break

        data = r.json()
        with open(f"{save_dir}/{i:04d}.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)

        pages = data["query"]["allpages"]
        data_count += len(pages)
        i += 1
        if i % 7 == 0:
            time.sleep(2)
        if i % 17 == 0:
            time.sleep(4)
            headers = {"User-Agent": ua.random}
        if i % 37 == 0:
            time.sleep(5)

        if "continue" in data:
            params.update(data["continue"])  # 翻页继续
            logging.info(f"page = {i}, count = {data_count}, {data['continue']}")
            time.sleep(0.1 + random.random() * 3)
        else:
            break


if __name__ == "__main__":
    fmt = "%(asctime)s %(filename)s [line:%(lineno)d] %(levelname)s %(message)s"
    logging.basicConfig(level=logging.INFO, format=fmt)

    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=str, default="out")
    parser.add_argument("--limit", type=int, default=-1)
    parser.add_argument("--restart", action="store_true")

    args = parser.parse_args()
    logging.info(f"args = {args}")
    try:
        fetch_all_titles(args.output, args.limit, args.restart)
    except Exception as e:
        logging.error(f"Exception = {e}")
