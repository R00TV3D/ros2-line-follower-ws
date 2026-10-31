import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/rugved-raut/Desktop/Rugved IIT BBS/ros2_ws/src/install/line_follower_pkg'
