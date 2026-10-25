"""python test_poster.py photo.jpg [inset.jpg]  -> preview1.jpg, preview2.jpg"""
import sys
from PIL import Image
import poster

photo = Image.open(sys.argv[1]).convert("RGB")
inset = Image.open(sys.argv[2]).convert("RGB") if len(sys.argv) > 2 else None
open("preview1.jpg", "wb").write(poster.make_poster(
    photo, "अनंत सिंह का नीरज कुमार पर तंज!",
    "बोले- ‘मेरी मिठाई बर्बाद नहीं होगी, नीरज जी भी भेज दें… वो भी खपा देंगे’"))
open("preview2.jpg", "wb").write(poster.make_poster_quote(
    photo, "गद्दारों को कर्मों की सजा मिल रही है, बुरे कर्म का बुरा नतीजा",
    "RJD ने अनंत सिंह पर साधा निशाना", inset))
print("preview1.jpg, preview2.jpg ready")
