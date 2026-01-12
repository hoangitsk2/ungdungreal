# Raspberry Pi Music Player

Ứng dụng Tkinter + pygame phát nhạc với giao diện hiện đại cho Raspberry Pi 4. Ứng dụng tự khởi động phát nhạc, chuyển ngẫu nhiên giữa các bài dưới 15 phút và tự tắt Raspberry Pi sau tổng cộng 15 phút phát.

## Tính năng chính
- Khởi động tự động phát nhạc khi mở ứng dụng.
- Giao diện đẹp với nền gradient, bảng playlist (double-click để phát), nút Play/Stop/Pause-Resume, nút chọn bài, nút phát ngẫu nhiên.
- Thanh trượt điều chỉnh âm lượng.
- Hiển thị tên bài hát và thời gian đã phát, đếm ngược thời gian còn lại trước khi tắt máy.
- Thêm bài nhanh bằng hộp thoại chọn nhiều file; hỗ trợ MP3/WAV/OGG/FLAC; playlist được lưu ở `playlist.txt` để lần sau mở lên vẫn giữ nguyên.
- Tự tắt Raspberry Pi sau 15 phút (có thể bật chế độ thử `DRY_RUN_SHUTDOWN=1`).

## Cài đặt
```bash
sudo apt update && sudo apt install python3 python3-pip python3-tk -y
pip3 install -r requirements.txt
```

## Chuẩn bị nhạc
- Thư mục `music/` đã có sẵn trong bộ mã nguồn; hãy chép file nhạc (.mp3, .wav, .ogg, .flac) trực tiếp vào đây để ứng dụng tự nhận. Nếu playlist đang trống, ứng dụng sẽ phát bài đầu tiên trong thư mục này.
- Mỗi playlist riêng được lưu dưới dạng file `.txt` trong thư mục `playlists/` (được tạo sẵn). Đường dẫn nên ghi tương đối tới `music/` để tiện mang app đi nơi khác.
- Nút **Add music** sẽ sao chép file bạn chọn vào thư mục `music/` (tự đổi tên nếu trùng) rồi thêm vào playlist đang mở và lưu lại file `.txt` tương ứng.

## Quản lý playlist trực quan
- Danh sách playlist nằm bên trái, có scrollbar; double-click vào bài để phát ngay.
- Chọn nhiều file một lúc bằng nút **Add music** để thêm nhanh vào playlist (không trùng lặp).
- Nút **Play random / Next random** sẽ chuyển sang bài khác bất kỳ và cập nhật highlight trong danh sách.
- Khi ứng dụng đang dừng, click chọn một bài sẽ hiển thị trước tên bài; bấm **Play** để phát hoặc double-click để phát luôn.
- Nút **New playlist** cho phép tạo nhiều playlist khác nhau; chọn playlist bằng combobox phía trên danh sách để chuyển nhanh.

## Chạy ứng dụng thủ công
```bash
python3 app.py
```
Đặt biến `DRY_RUN_SHUTDOWN=1` khi chạy nếu muốn thử mà không tắt máy:
```bash
DRY_RUN_SHUTDOWN=1 python3 app.py
```

### Chạy thử trên Windows
- Cài Python 3, Tkinter (đi kèm Python) và `pip install -r requirements.txt`.
- Lệnh tắt máy mặc định sẽ tự động dùng `shutdown /s /t 0` trên Windows; để tránh tắt máy khi thử, đặt `DRY_RUN_SHUTDOWN=1` hoặc ghi đè lệnh bằng `PLAYER_SHUTDOWN_COMMAND="shutdown /a"`.
- Kiểm tra mã nguồn nhanh bằng:
```bash
python -m py_compile app.py
```

## Thiết lập tự khởi động khi bật Raspberry Pi
Tạo service systemd để ứng dụng mở cùng hệ thống và tự phát nhạc:
```bash
sudo tee /etc/systemd/system/pimusic.service <<'EOF'
[Unit]
Description=Pi Music Player
After=network.target sound.target

[Service]
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/pi/.Xauthority
WorkingDirectory=/home/pi/ungdungreal
ExecStart=/usr/bin/python3 /home/pi/ungdungreal/app.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now pimusic.service
```
Điều chỉnh `WorkingDirectory` và đường dẫn trong `ExecStart` nếu bạn lưu mã nguồn ở vị trí khác. Nếu đang thử nghiệm và không muốn tắt máy, thêm `Environment=DRY_RUN_SHUTDOWN=1` vào phần `[Service]`.

## Thay đổi lệnh tắt máy
Mặc định, ứng dụng chạy `sudo shutdown -h now` sau 15 phút. Bạn có thể thay lệnh bằng biến môi trường, ví dụ để khởi động lại:
```bash
PLAYER_SHUTDOWN_COMMAND="sudo reboot"
```

## Lưu ý vận hành
- Ứng dụng sẽ phát bài tiếp theo ngẫu nhiên nếu bài hiện tại kết thúc trước khi đủ 15 phút tổng thời gian phát.
- Nếu không có bài trong playlist, ứng dụng chờ bạn thêm nhạc và không tự tắt cho tới khi đủ 15 phút kể từ khi mở (hãy dùng `DRY_RUN_SHUTDOWN=1` khi thử nghiệm).
