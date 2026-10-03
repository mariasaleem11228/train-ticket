# Avatar migration checkpoint

Avatar is Spring Modulith business module 40. The Java module owns `POST /api/v1/avatar` and calls the existing dlib/OpenCV face detector as a local utility in the same container. There is no remote Avatar HTTP call on the module route. The native algorithm remains Python code, so replacing that utility with a Java/native binding is future cleanup if a single JVM process is required.

The live Python service, isolated module candidate, and browser route produced the same status and response for a face image, a blank image, and a missing `img` field. The face crop was byte-for-byte identical. `mvn -f ts-modulith/pom.xml test package` and the full hybrid checkpoint passed with 40 modules. A module-to-legacy-to-module rollback rehearsal returned the identical crop on each route.

The UI is `http://localhost:8080/upload_avatar.html`. Upload a clear face image, then inspect `POST /api/v1/avatar` in DevTools: it should return 200, the cropped image should appear, and the response header should be `X-Avatar-Backend: module`. Run `python docs/migration/verify_checkpoint.py` for the live checkpoint or `python docs/migration/verify_avatar_rollback.py` for the rollback rehearsal.

Delivery was subsequently ported as module 41. WaitOrder and Food Delivery remain outside the running Compose stack.
