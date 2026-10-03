# News migration checkpoint

News is Spring Modulith business module 38. It is an independent, read-only module. Its Go implementation returns the same fixed body for all GET paths and declares `text/html; charset=utf-8`; the Java module preserves that deployed HTTP contract on the `/news-service/**` route. The legacy service has no active MongoDB read path: that source code is commented out.

Avatar remains on its Python dlib implementation. Its face detection and crop output need image-based contract comparisons before cutover, so News was moved ahead of it in the sequence.

The News compatibility proxy preserves the `ts-news-service:12862` identity for the UI and can switch independently between Go and the shared host. Run `python docs/migration/verify_checkpoint.py` for the full hybrid check and `python docs/migration/verify_news_rollback.py` for a read-only rollback rehearsal. The old UI page is `http://localhost:8080/old_index.html`; its News refresh button calls `GET /news-service/news`. The response should have `X-News-Backend: module`.
