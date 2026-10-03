"""One-shot local adapter for the deployed Avatar service's dlib/OpenCV algorithm."""
import base64
import contextlib
import io
import json
import sys
import traceback

import cv2
import numpy as np
from face_detect import check


def main():
    try:
        image_b64 = sys.stdin.buffer.read()
        image_bytes = base64.b64decode(image_b64)
        image = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
        # The original detector prints progress; keep stdout reserved for the response.
        with contextlib.redirect_stdout(sys.stderr):
            result = check(image)
        if isinstance(result, dict):
            sys.stdout.write(json.dumps(result, separators=(',', ':')) + '\n')
            return 2
        sys.stdout.buffer.write(result)
        return 0
    except Exception:
        sys.stdout.write(json.dumps({'msg': 'exception:' + traceback.format_exc()}) + '\n')
        return 1


if __name__ == '__main__':
    sys.exit(main())
