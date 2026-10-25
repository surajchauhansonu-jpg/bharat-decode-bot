"""python test_poster.py photo.jpg  -> preview.jpg banata hai."""
import sys
from PIL import Image
import poster

photo = Image.open(sys.argv[1]).convert("RGB")
jpg = poster.make_poster(photo, "अनंत सिंह का नीरज कुमार पर तंज!",
                         "बोले- ‘मेरी मिठाई बर्बाद नहीं होगी, नीरज जी भी भेज दें… वो भी खपा देंगे’")
open("preview.jpg", "wb").write(jpg)
print("preview.jpg ready")
