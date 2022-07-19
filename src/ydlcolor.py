'''
    ydlcolor.py
    
    Youtube Downloader: Create Download List from URL w/ list type

    Author: Uisang Hwang
    
'''
from PyQt5.QtGui import QColor
#from PyQt4.QtGui import QColor

_ydl_color_error      = QColor(247,79,83)
_ydl_color_file_exist = QColor(158,248,160)
_ydl_color_finished   = QColor(230,213,89)
_ydl_color_white      = QColor(255,255,255)


def TG_HSV_To_RGB(H, S, V):
	import math
	I = 0.0
	F = 0.0
	P = 0.0
	Q = 0.0
	T = 0.0
	R1 = 0.0
	G1 = 0.0
	B1 = 0.0
	
	if S == 0:
		if H <= 0 or H > 360 :
			return (V,V,V)

	if H==360: H=0

	H = H/60;
	I = math.floor(H)
	F = H-I
	P = V*(1-S)
	Q = V*(1-S*F)
	T = V*(1-S*(1-F))
	
	int_I = int(I)
	
	if   int_I == 0: 
		R1 = V
		G1 = T
		B1 = P
	elif int_I == 1: 
		R1 = Q
		G1 = V
		B1 = P
	elif int_I == 2: 
		R1 = P
		G1 = V
		B1 = T
	elif int_I == 3: 
		R1 = P
		G1 = Q
		B1 = V
	elif int_I == 4: 
		R1 = T
		G1 = P
		B1 = V
	else           : 
		R1 = V
		G1 = P
		B1 = Q
	
	R = int(R1 * 255)
	G = int(G1 * 255)
	B = int(B1 * 255)

	return (R,G,B)
    
  