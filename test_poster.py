"""python test_poster.py photo.jpg  -> preview_A.jpg, preview_B.jpg"""
import sys
from PIL import Image
import poster

photo = Image.open(sys.argv[1]).convert("RGB")
open("preview_A.jpg", "wb").write(poster.make_poster(
    photo, "अनंत सिंह का नीरज कुमार पर तंज!",
    "बोले- ‘मेरी मिठाई बर्बाद नहीं होगी, नीरज जी भी भेज दें… वो भी खपा देंगे’"))
open("preview_B.jpg", "wb").write(poster.make_poster(
    photo, "गद्दारों को कर्मों की सजा मिल रही है, बुरे कर्म का बुरा नतीजा",
    "- RJD ने अनंत सिंह पर साधा निशाना"))
print("preview_A.jpg, preview_B.jpg ready")
