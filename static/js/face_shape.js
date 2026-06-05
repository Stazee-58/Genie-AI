$(document).ready(function () {

    // ─── Upload file (cũ) ────────────────────────────────────────
    $("#upload_button").click(function () {
        $("#fileinput").trigger("click");
    });

    $("#fileinput").change(function () {
        $("#upload_hint").text("Đang tải file " + $("#fileinput")[0].files[0].name + " lên server...");
        $("#form").submit();
    });

    // ─── Camera ──────────────────────────────────────────────────
    let stream = null;

    function stopCamera() {
        if (stream) {
            stream.getTracks().forEach(t => t.stop());
            stream = null;
        }
        $("#video-stream").hide().attr("srcObject", null)[0].srcObject = null;
        $("#snap_button").hide();
        $("#stop_button").hide();
        $("#camera_button").show();
        $("#cam-hint").text("");
    }

    // Bật camera
    $("#camera_button").click(async function () {
        try {
            stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "user" }, audio: false });
            const video = document.getElementById("video-stream");
            video.srcObject = stream;
            video.style.display = "block";
            $("#camera_button").hide();
            $("#snap_button").show();
            $("#stop_button").show();
            $("#cam-hint").text("Hãy nhìn thẳng vào camera, sau đó nhấn '📸 Chụp & Phân tích'");
        } catch (err) {
            $("#cam-hint").text("Không thể truy cập camera: " + err.message);
        }
    });

    // Tắt camera
    $("#stop_button").click(function () {
        stopCamera();
    });

    // Chụp ảnh và gửi lên server
    $("#snap_button").click(function () {
        const video  = document.getElementById("video-stream");
        const canvas = document.getElementById("canvas-snap");
        canvas.width  = video.videoWidth  || 480;
        canvas.height = video.videoHeight || 360;
        canvas.getContext("2d").drawImage(video, 0, 0, canvas.width, canvas.height);

        $("#cam-hint").text("Đang phân tích khuôn mặt...");
        $("#snap_button").prop("disabled", true);

        // Chuyển canvas → Blob → File → FormData → POST
        canvas.toBlob(function (blob) {
            const formData = new FormData();
            formData.append("file", blob, "snapshot.jpg");
            stopCamera();

            $.ajax({
                url: "/face_shape",
                type: "POST",
                data: formData,
                processData: false,
                contentType: false,
                success: function (html) {
                    // Thay toàn bộ trang bằng phản hồi từ server
                    document.open();
                    document.write(html);
                    document.close();
                },
                error: function () {
                    $("#cam-hint").text("Lỗi khi gửi ảnh. Vui lòng thử lại.");
                    $("#snap_button").prop("disabled", false);
                }
            });
        }, "image/jpeg", 0.92);
    });
});
