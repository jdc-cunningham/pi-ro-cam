import os
import sys
import time
import spidev as SPI
import math

base_path = os.getcwd()

sys.path.append(base_path + "/display/")

from lib import LCD_2inch4
from PIL import Image, ImageDraw, ImageFont
from threading import Thread

RST = 27
DC = 25
BL = 18
bus = 0
device = 0

battery_sprite_path = base_path + "/menu/menu-sprites/battery_25_15.jpg"
folder_sprite_path = base_path + "/menu/menu-sprites/folder_21_18.jpg"
gear_sprite_path = base_path + "/menu/menu-sprites/gear_23_20.jpg"

small_font = ImageFont.truetype(base_path + "/display/Font/Font00.ttf", 13)
large_font = ImageFont.truetype(base_path + "/display/Font/Font02.ttf", 16)
larger_font = ImageFont.truetype(base_path + "/display/Font/Font02.ttf", 24)

class Display:
  def __init__(self, main):
    self.dimensions = [240, 320] # should be dynamically generated from library
    self.main = main
    self.active_img = None
    self.active_icon = None
    self.utils = main.utils
    self.file_count = self.utils.get_file_count() # maybe shouldn't be here
    self.disp = None
    self.formatted_time = 0

    self.setup_lcd()

  def setup_lcd(self):
    self.disp = LCD_2inch4.LCD_2inch4()
    self. disp.Init()
    self.disp.clear()

  def stamp_img(self, pil_img):
    img = ImageDraw.Draw(pil_img)

    focus_text = 'AF' if self.main.focus_level == -1 else 'F ' + str(self.main.focus_level)

    img.text((270, 280), focus_text, fill = (255,255,255), font=larger_font)

    return pil_img
  
  def check_leading_zero(self, num):
    if (num < 10):
      return "0" + str(num)
    else:
      return str(num)
  
  def format_time(self, seconds):
    if (seconds > 60):
      return self.check_leading_zero(math.floor(seconds / 60)) + ":" + self.check_leading_zero(seconds % 60)
    else:
      return "0:" + self.check_leading_zero(seconds)

  def match_lcd(self, image, camera_frame = False):
    if (camera_frame == "video"):
      c_img = image.crop((0, 0, 320, 320))

      # draw elapsed time and pulsing red dot
      # lol access camera from main
      video_start_time = self.main.camera.recording_time
      elapsed_time = time.time() - video_start_time

      # when video ends, can show super long number
      if (video_start_time > 0):
        self.formatted_time = self.format_time(math.floor(elapsed_time))
      
      draw = ImageDraw.Draw(c_img)
      draw.ellipse((10, 300, 20, 310), fill=(255,0,0,0))
      x_pos = 30 if len(self.formatted_time) > 4 else 25
      draw.text((x_pos, 295), self.formatted_time, fill = "white", font = large_font)

      r_img = c_img.rotate(-90)

      base_image = Image.new("RGB", (240, 320), "WHITE")
      base_image.paste(r_img, (0, 0))

      f_img = base_image
    elif (camera_frame):
      r_img = image.rotate(-90)
      c_img = r_img.crop((0, 0, 240, 320))
      f_img = c_img
    else:
      base_image = Image.new("RGB", (240, 320), "WHITE")
      c_img = image
      r_img = c_img.rotate(-90)
      base_image.paste(r_img, (-80, 0))
      f_img = base_image

    return f_img

  def render_menu_base(self, center_text = "Camera on", photo_text = "photo"):
    image = Image.new("RGB", (320, 320), "WHITE")
    draw = ImageDraw.Draw(image)

    draw.text((7, 3), photo_text, fill = "BLACK", font = small_font)
    draw.text((7, 105), "Auto", fill = "BLACK", font = small_font)
    # manual photography mode
    # draw.text((7, 90), "S: 1/60", fill = "WHITE", font = small_font)
    # draw.text((7, 105), "E: 100", fill = "WHITE", font = small_font)
    draw.text((22, 48), center_text, fill = "BLACK", font = large_font)
    processing_text = len(self.main.camera.video_processing) > 0

    if (processing_text):
      draw.text((22, 60), "video processing", fill = "BLACK", font = small_font)

    draw.text((58, 3), self.main.battery.get_remaining_time(), fill = "BLACK", font = small_font)

    file_count = self.utils.get_file_count()

    draw.text((60 if file_count < 100 else 55, 103), str(file_count), fill = "BLACK", font = small_font)

    battery_icon = Image.open(battery_sprite_path)
    folder_icon = Image.open(folder_sprite_path)
    gear_icon = Image.open(gear_sprite_path)

    image.paste(battery_icon, (98, 5))
    image.paste(folder_icon, (77, 103))
    image.paste(gear_icon, (101, 102))

    return image

  def start_menu(self):
    menu_base = self.render_menu_base()

    self.disp.ShowImage(self.match_lcd(menu_base))

  def display_image(self, img_path):
    image = Image.open(img_path)
    self.disp.ShowImage(self.match_lcd(image))

  def show_image(self, img, camera_type = False):
    self.disp.ShowImage(self.match_lcd(img, camera_type))

  def clear_screen(self):
    self.disp.clear()

  def show_boot_scene(self):
    image = Image.new("RGB", (320, 320), "WHITE")
    draw = ImageDraw.Draw(image)

    # look right
    draw.line([(20, 40), (50, 40)], fill = "BLACK", width = 3) # left eyebrow
    draw.line([(33, 44), (50, 44)], fill = "BLACK", width = 6) # left eye
    draw.line([(38, 48), (48, 48)], fill = "BLACK", width = 2) # left eye bottom

    draw.line([(75, 40), (105, 40)], fill = "BLACK", width = 3) # right eyebrow
    draw.line([(88, 44), (105, 44)], fill = "BLACK", width = 6) # right eye
    draw.line([(93, 48), (103, 48)], fill = "BLACK", width = 2) # right eye bottom

    draw.line([(40, 95), (35, 93)], fill = "BLACK", width = 1)  # mouth left
    draw.line([(40, 95), (90, 95)], fill = "BLACK", width = 1)  # mouth

    self.disp.ShowImage(self.match_lcd(image))

    time.sleep(1)

    image = Image.new("RGB", (320, 320), "WHITE")
    draw = ImageDraw.Draw(image)

    # wink
    draw.line([(20, 45), (50, 45)], fill = "BLACK", width = 3) # left eyebrow

    draw.line([(75, 40), (105, 40)], fill = "BLACK", width = 3) # right eyebrow
    draw.line([(88, 44), (105, 44)], fill = "BLACK", width = 6) # right eye
    draw.line([(93, 48), (103, 48)], fill = "BLACK", width = 2) # right eye bottom

    draw.line([(40, 95), (35, 93)], fill = "BLACK", width = 1)  # mouth left
    draw.line([(40, 95), (90, 95)], fill = "BLACK", width = 1)  # mouth

    self.disp.ShowImage(self.match_lcd(image))

    time.sleep(0.5)

    image = Image.new("RGB", (320, 320), "WHITE")
    draw = ImageDraw.Draw(image)

    # look right
    draw.line([(20, 40), (50, 40)], fill = "BLACK", width = 4)  # left eyebrow
    draw.line([(35, 45), (50, 45)], fill = "BLACK", width = 5)  # left eye
    draw.line([(38, 48), (48, 48)], fill = "BLACK", width = 2)  # left eye bottom

    draw.line([(75, 40), (105, 40)], fill = "BLACK", width = 4) # right eyebrow
    draw.line([(90, 45), (105, 45)], fill = "BLACK", width = 5) # right eye
    draw.line([(93, 48), (103, 48)], fill = "BLACK", width = 2) # right eye bottom

    draw.line([(40, 95), (35, 93)], fill = "BLACK", width = 1)  # mouth left
    draw.line([(40, 95), (90, 95)], fill = "BLACK", width = 1)  # mouth

    self.disp.ShowImage(self.match_lcd(image))

    time.sleep(1)

    image = Image.new("RGB", (320, 320), "WHITE")
    draw = ImageDraw.Draw(image)

    draw.text((20, 55), "Modular Pi Cam", fill = "BLACK", font = large_font)
    draw.text((20, 70), "", fill = "BLACK", font = small_font)

    self.disp.ShowImage(self.match_lcd(image))

    time.sleep(3)

    self.clear_screen()

  def set_menu_center_text(self, draw, text, x = 22, y = 48):
    draw.text((x, y), text, fill = "BLACK", font = large_font)

  def draw_active_icon(self, icon_name):
    image = self.render_menu_base("")
    draw = ImageDraw.Draw(image)

    if (icon_name == "Files"):
      draw.line([(60, 121), (98, 121)], fill = "BLUE", width = 2)
      self.set_menu_center_text(draw, "Files")

    if (icon_name == "Camera Settings"):
      draw.line([(7, 121), (34, 121)], fill = "BLUE", width = 2)
      self.set_menu_center_text(draw, "Camera Settings", 5)

    if (icon_name == "Photo Video Toggle"):
      draw.line([(7, 22), (34, 22)], fill = "BLUE", width = 2)
      self.set_menu_center_text(draw, "Toggle Mode")

    if (icon_name == "Settings"):
      draw.line([(101, 122), (124, 122)], fill = "BLUE", width = 2)
      self.set_menu_center_text(draw, "Settings")
    
    self.disp.ShowImage(self.match_lcd(image))
  
  def toggle_text(self, mode):
    if (mode == "video"):
      image = self.render_menu_base("Tap to record", "video")
    else:
      image = self.render_menu_base("Toggle Mode", "photo")

    self.disp.ShowImage(self.match_lcd(image))

  def draw_text(self, text):
    image = Image.new("RGB", (320, 320), "WHITE")
    draw = ImageDraw.Draw(image)
    font = large_font

    draw.text((0, 96), text, fill = "BLACK", font = font)

    self.disp.ShowImage(self.match_lcd(image))

  def get_settings_img(self):
    image = Image.new("RGB", (320, 320), "WHITE")
    draw = ImageDraw.Draw(image)

    draw.line([(0, 0), (320, 0)], fill = "BLACK", width = 40)
    draw.text((5, 0), "Settings", fill = "WHITE", font = large_font)
    draw.text((5, 26), "Telemetry", fill = "BLACK", font = large_font)
    draw.text((5, 52), "Battery Profiler", fill = "BLACK", font = large_font)
    draw.text((5, 78), "Reset Battery", fill = "BLACK", font = large_font)
    draw.text((5, 104), "Timelapse", fill = "BLACK", font = large_font)
    draw.text((5, 130), "Transfer To USB", fill = "BLACK", font = large_font)
    draw.text((5, 156), "Delete All Files", fill = "BLACK", font = large_font)

    return image
  
  def render_settings(self):
    image = self.get_settings_img()

    self.disp.ShowImage(self.match_lcd(image))

  def render_battery_profiler(self):
    image = Image.new("RGB", (320, 320), "WHITE")
    draw = ImageDraw.Draw(image)

    draw.text((0, 48), "Profiling battery", fill = "BLACK", font = large_font)
    draw.text((0, 72), "Press back to cancel", fill = "BLACK", font = small_font)

    self.disp.ShowImage(self.match_lcd(image))

  def render_timelapse(self):
    image = Image.new("RGB", (320, 320), "WHITE")
    draw = ImageDraw.Draw(image)

    draw.text((0, 48), "5 min timelapse", fill = "BLACK", font = large_font)
    draw.text((0, 72), "Press back to cancel", fill = "BLACK", font = small_font)

    self.disp.ShowImage(self.match_lcd(image))

  def render_delete_all_files(self, active_yes = False):
    image = Image.new("RGB", (320, 320), "WHITE")
    draw = ImageDraw.Draw(image)

    draw.text((22, 48), "Delete All Files?", fill = "BLACK", font = large_font)
    draw.text((22, 72), "Yes", fill = "BLUE" if (active_yes) else "BLACK", font = small_font)
    draw.text((60, 72), "No", fill = "BLACK" if (active_yes) else "BLUE", font = small_font)

    self.disp.ShowImage(self.match_lcd(image))

  def render_usb_transfer(self, msg = ""):
    image = Image.new("RGB", (320, 320), "WHITE")
    draw = ImageDraw.Draw(image)

    draw.text((22, 48), msg, fill = "BLACK", font = small_font)

    self.disp.ShowImage(self.match_lcd(image))

  def render_battery_charged(self, is_charged = False):
    image = Image.new("RGB", (320, 320), "WHITE")
    draw = ImageDraw.Draw(image)

    draw.text((22, 48), "Battery Charged?", fill = "BLACK", font = small_font)
    draw.text((22, 72), "Yes", fill = "BLUE" if is_charged else "BLACK", font = small_font)
    draw.text((60, 72), "No", fill = "BLACK" if is_charged else "BLUE", font = small_font) # default option

    self.disp.ShowImage(self.match_lcd(image))

  def draw_active_telemetry(self):
    image = self.get_settings_img()
    draw = ImageDraw.Draw(image)

    draw.line([(0, 26), (0, 42)], fill = "BLUE", width = 2) # 16 tall, 10 y apart

    self.disp.ShowImage(self.match_lcd(image))

  def draw_active_battery_profiler(self):
    image = self.get_settings_img()
    draw = ImageDraw.Draw(image)

    draw.line([(0, 52), (0, 68)], fill = "BLUE", width = 2)

    self.disp.ShowImage(self.match_lcd(image))

  def draw_active_reset_battery(self):
    image = self.get_settings_img()
    draw = ImageDraw.Draw(image)

    draw.line([(0, 78), (0, 94)], fill = "BLUE", width = 2)

    self.disp.ShowImage(self.match_lcd(image))

  def draw_active_timelapse(self):
    image = self.get_settings_img()
    draw = ImageDraw.Draw(image)

    draw.line([(0, 104), (0, 120)], fill = "BLUE", width = 2)

    self.disp.ShowImage(self.match_lcd(image))

  def draw_active_transfer_to_usb(self):
    image = self.get_settings_img()
    draw = ImageDraw.Draw(image)

    draw.line([(0, 130), (0, 146)], fill = "BLUE", width = 2)

    self.disp.ShowImage(self.match_lcd(image))

  def draw_active_delete_all_files(self):
    image = self.get_settings_img()
    draw = ImageDraw.Draw(image)

    draw.line([(0, 156), (0, 172)], fill = "BLUE", width = 2)

    self.disp.ShowImage(self.match_lcd(image))

  # this is not advanced eg. a thread where it can detect USB plugged in here
  def render_transfer_to_usb(self, transfer = False):
    image = Image.new("RGB", (320, 320), "WHITE")
    draw = ImageDraw.Draw(image)

    draw.text((22, 48), "UBS Not Detected" if self.main.usb == None else "USB Detected", fill = "BLACK", font = small_font)
    draw.text((22, 72), "Transfer", fill = "BLUE" if (transfer) else "BLACK", font = small_font)
    draw.text((80, 72), "Cancel", fill = "BLACK" if (transfer) else "BLUE", font = small_font)

    self.disp.ShowImage(self.match_lcd(image))

  def render_deleting_files(self, msg = ""):
    image = Image.new("RGB", (320, 320), "WHITE")
    draw = ImageDraw.Draw(image)

    draw.text((22, 48), msg if (msg) else "Deleting Files...", fill = "BLACK", font = small_font)

    self.disp.ShowImage(self.match_lcd(image))

  def render_live_telemetry(self):
    while (self.main.menu.active_menu_item == "Telemetry"):
      image = Image.new("RGB", (320, 320), "WHITE")
      draw = ImageDraw.Draw(image)

      accel = self.main.imu.accel
      gyro = self.main.imu.gyro

      draw.line([(0, 0), (320, 0)], fill = "BLACK", width = 40)
      draw.text((5, 0), "Raw Telemetry", fill = "WHITE", font = large_font)
      draw.text((5, 26), "accel x: " + str(accel[0])[0:8], fill = "BLACK", font = small_font)
      draw.text((5, 36), "accel y: " + str(accel[1])[0:8], fill = "BLACK", font = small_font)
      draw.text((5, 46), "accel z: " + str(accel[2])[0:8], fill = "BLACK", font = small_font)
      draw.text((5, 56), "gyro x: " + str(gyro[0])[0:8], fill = "BLACK", font = small_font)
      draw.text((5, 66), "gyro y: " + str(gyro[1])[0:8], fill = "BLACK", font = small_font)
      draw.text((5, 76), "gyro z: " + str(gyro[2])[0:8], fill = "BLACK", font = small_font)

      self.disp.ShowImage(self.match_lcd(image))
    
  # special page, it is not static
  # has active loop to display data
  def render_telemetry_page(self):
    # this is not good, brought in main context into display to pull imu values
    Thread(target=self.render_live_telemetry).start()
  
  # this will need a background process to generate thumbnails
  # since it takes 5+ seconds to do the step below/show files

  # this takes a list of img file paths (up to 4)
  # if it's a video, need ffmpeg to get a thumbnail (future)
  # render the OLED scene with these images and pagination footer
  # yeah this is hard, need offsets
  # https://stackoverflow.com/a/451580
  def get_files_scene(self, file_paths, page, pages):
    image = Image.new("RGB", (320, 320), "WHITE")
    draw = ImageDraw.Draw(image)
    base_img_path = base_path + "/captured-media/"

    # this is dumb, my brain is blocked right now, panicking, too much to do
    # this code has to be reworked anyway this is like a demo
    page_map = [[], [0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11]] # matches file list

    new_size = (45, 45)

    files = page_map[page]
    
    for file in files:
      cam_image = Image.open(base_img_path + file_paths[file])
      base_width= 45
      wpercent = (base_width / float(cam_image.size[0]))
      hsize = int((float(cam_image.size[1]) * float(wpercent)))
      cam_image = cam_image.resize((base_width, hsize), resample=Image.LANCZOS)

      # this is dumb
      if (file == 0):
        image.paste(cam_image, (15, 7))
      if (file == 1):
        image.paste(cam_image, (67, 7))
      if (file == 2):
        image.paste(cam_image, (15, 60))
      if (file == 3):
        image.paste(cam_image, (67, 60))

    if (page > 1):
      draw.text((7, 110), "<", fill = "BLACK", font = small_font)

    draw.text((50, 110), str(page) + "/" + str(pages), fill = "BLACK", font = small_font)

    if (pages > 1):
      draw.text((110, 110), ">", fill = "BLACK", font = small_font)

    return image

  def render_files(self):
    files = self.utils.get_files()
    file_count = len(files)
    self.main.menu.files_pages = 1 if ((file_count / 4) < 1) else math.ceil(file_count / 4)

    if (file_count == 0):
      self.draw_text("No Files")
    else:
      self.main.active_menu = "Files"
      files_scene = self.get_files_scene(files, self.main.menu.files_page, self.main.menu.files_pages)
      self.disp.ShowImage(self.match_lcd(files_scene))