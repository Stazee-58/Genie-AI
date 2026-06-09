$(document).ready(function () {
    // ─── Upload file ─────────────────────────────────────────────
    $("#upload_button").click(function () {
        $("#fileinput").trigger("click");
    });

    $("#fileinput").change(function () {
        $("#upload_hint").text("Đang tải file " + $("#fileinput")[0].files[0].name + " lên server...");
        $("#form").submit();
    });

    // ─── Camera logic ────────────────────────────────────────────
    let stream = null;

    function stopCamera() {
        if (stream) {
            stream.getTracks().forEach(t => t.stop());
            stream = null;
        }
        const video = document.getElementById("video-stream");
        video.style.display = "none";
        video.srcObject = null;
        $("#camera_button").show();
        $("#snap_button").hide();
        $("#stop_button").hide();
        $("#camera-hint").text("");
    }

    $("#camera_button").click(async function () {
        try {
            stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "user" }, audio: false });
            const video = document.getElementById("video-stream");
            video.srcObject = stream;
            video.style.display = "block";
            $("#camera_button").hide();
            $("#snap_button").show();
            $("#stop_button").show();
            $("#camera-hint").text("Hãy nhìn thẳng vào camera, sau đó nhấn '📸 Chụp & Phân tích'");
        } catch (err) {
            $("#camera-hint").text("Không thể truy cập camera: " + err.message);
        }
    });

    $("#stop_button").click(function () {
        stopCamera();
    });

    $("#snap_button").click(function () {
        const video = document.getElementById("video-stream");
        const canvas = document.getElementById("canvas-snap");
        canvas.width = video.videoWidth || 480;
        canvas.height = video.videoHeight || 360;
        const ctx = canvas.getContext("2d");
        ctx.translate(canvas.width, 0);
        ctx.scale(-1, 1);
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

        $("#camera-hint").text("Đang phân tích sắc màu cá nhân...");
        $("#snap_button").prop("disabled", true);

        // Chuyển canvas → Blob → File → FormData → POST
        canvas.toBlob(function (blob) {
            const formData = new FormData();
            formData.append("file", blob, "snapshot_pc.jpg");
            stopCamera();

            $.ajax({
                url: "/personal_color",
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
                    $("#camera-hint").text("Lỗi khi gửi ảnh. Vui lòng thử lại.");
                    $("#snap_button").prop("disabled", false);
                }
            });
        }, "image/jpeg", 0.92);
    });
});
