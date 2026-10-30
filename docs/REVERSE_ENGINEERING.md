# Home AI inspection — uploaded split bundle

The five user-supplied parts aa–ae were concatenated in order. ZIP CRC integrity check passed. Bundle SHA256: 05dd263962534388692ae4494df1d0ef30b8dcab275f36d3cfbd07ef23a24227.
This verifies transfer consistency, not publisher certificate trust.

REA Evidence: ev_764d560fd4a28e4fa795100ebf0e008c82b88f28d0816c371d4be1360625fbf0

Verified with REA inspect-android-package and checksum-verified jadx-headless-mcp 0.7.1:
- Package interior.home.design.ai, version 1.9.6, version code 133.
- Minimum Android API 31; target API 36.
- Full decoded manifest retained in artifacts/AndroidManifest.xml.
- Complete REA response retained in artifacts/package-evidence.json.

Archive observations:
- Base APK and ABI, density and language split APKs extracted into artifacts/.
- assets/index.android.bundle is Hermes bytecode v96, not plain JavaScript source.
- Packaged SF Pro Display fonts and Technology.ttf exist.
- 979 resource image/XML entries inventoried in artifacts/resource-inventory.json.
- prod_android_fallback.json contains paywall/offer configuration, not an established generation API.
- No uploaded executable was launched and no production service was called.

Unresolved: screen rendering and navigation at runtime, Hermes application logic, generation service authorization, genuine SKU-conditioned generation and exact UI equivalence. The existing Roomform prototype remains an independent implementation and is not an unchanged Home AI build. No APK modifications, original AI service integration or used-furniture feature completion are claimed.

User requirements: preserve existing end-user screens and flows; add commercial furniture/decor vendor onboarding, individual secondhand sellers, listing price/condition/location/delivery details, actual-product placement and consultation/vendor matching. Changes must remain additive and cannot be verified as visually unchanged without runtime screen evidence.

The original APK and installed dependencies are retained locally, not committed. Original private backend access cannot be supplied by the APK alone. Do not reuse embedded credentials or infer service permission from static configuration.
