import os
import shutil

def create_project(project_dir, app_name):
    """
    从模板创建新的 Android 录音项目
    
    参数:
        project_dir: 新项目所在目录
        app_name: 应用名称 (如 "myrecorder")
    """
    
    app_id = f"com.{app_name}.app"
    package_path = app_id.replace(".", os.sep)
    
    # 模板路径
    template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "项目模板")
    if not os.path.exists(template_dir):
        print(f"错误: 找不到模板目录 {template_dir}")
        return
    
    # 创建项目目录
    os.makedirs(project_dir, exist_ok=True)
    print(f"✓ 创建项目目录: {project_dir}")
    
    # 复制模板文件
    def copy_template(src, dst):
        if os.path.isdir(src):
            os.makedirs(dst, exist_ok=True)
            for item in os.listdir(src):
                copy_template(os.path.join(src, item), os.path.join(dst, item))
        else:
            shutil.copy2(src, dst)
    
    copy_template(template_dir, project_dir)
    print(f"✓ 已复制模板文件")
    
    # 修改 app/build.gradle
    gradle_path = os.path.join(project_dir, "app", "build.gradle")
    if os.path.exists(gradle_path):
        with open(gradle_path, "r", encoding="utf-8") as f:
            content = f.read()
        content = content.replace("com.你的包名.app", app_id)
        with open(gradle_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✓ 已配置 app/build.gradle")
    
    # 修改 strings.xml
    strings_path = os.path.join(project_dir, "app", "src", "main", "res", "values", "strings.xml")
    if os.path.exists(strings_path):
        with open(strings_path, "w", encoding="utf-8") as f:
            f.write(f'<?xml version="1.0" encoding="utf-8"?>\n<resources>\n    <string name="app_name">{app_name}</string>\n</resources>\n')
        print(f"✓ 已配置 strings.xml")
    
    # 创建 MainActivity.kt
    java_dir = os.path.join(project_dir, "app", "src", "main", "java", package_path)
    os.makedirs(java_dir, exist_ok=True)
    
    main_activity = os.path.join(java_dir, "MainActivity.kt")
    with open(main_activity, "w", encoding="utf-8") as f:
        f.write(f'''package {app_id}

import android.Manifest
import android.content.pm.PackageManager
import android.media.MediaRecorder
import android.os.Build
import android.os.Bundle
import android.os.Environment
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import {app_id}.R

class MainActivity : AppCompatActivity() {{

    private var mediaRecorder: MediaRecorder? = null
    private var isRecording = false
    private var currentFilePath: String? = null

    companion object {{
        private const val PERMISSION_REQUEST_CODE = 100
    }}

    override fun onCreate(savedInstanceState: Bundle?) {{
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        setupButtons()
        checkPermissions()
    }}

    private fun setupButtons() {{
        findViewById<android.widget.Button>(R.id.btnStartRecording).setOnClickListener {{
            if (!isRecording) startRecording()
        }}

        findViewById<android.widget.Button>(R.id.btnStopRecording).setOnClickListener {{
            if (isRecording) stopRecording()
        }}
    }}

    private fun checkPermissions() {{
        val permissions = mutableListOf<String>()
        
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) 
            != PackageManager.PERMISSION_GRANTED) {{
            permissions.add(Manifest.permission.RECORD_AUDIO)
        }}

        if (Build.VERSION.SDK_INT <= Build.VERSION_CODES.P &&
            ContextCompat.checkSelfPermission(this, Manifest.permission.WRITE_EXTERNAL_STORAGE) 
            != PackageManager.PERMISSION_GRANTED) {{
            permissions.add(Manifest.permission.WRITE_EXTERNAL_STORAGE)
        }}

        if (permissions.isNotEmpty()) {{
            ActivityCompat.requestPermissions(this, permissions.toTypedArray(), PERMISSION_REQUEST_CODE)
        }}
    }}

    private fun startRecording() {{
        try {{
            val mp3Dir = File(getExternalFilesDir(null), "mp3")
            if (!mp3Dir.exists()) mp3Dir.mkdirs()

            val timestamp = java.text.SimpleDateFormat("yyyyMMdd_HHmmss", java.util.Locale.getDefault()).format(java.util.Date())
            val fileName = "recording_$timestamp.mp3"
            val outputFile = File(mp3Dir, fileName)
            currentFilePath = outputFile.absolutePath

            mediaRecorder = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {{
                MediaRecorder(this)
            }} else {{
                @Suppress("DEPRECATION")
                MediaRecorder()
            }}

            mediaRecorder?.apply {{
                setAudioSource(MediaRecorder.AudioSource.MIC)
                setOutputFormat(MediaRecorder.OutputFormat.MPEG_4)
                setAudioEncoder(MediaRecorder.AudioEncoder.AAC)
                setAudioEncodingBitRate(128000)
                setAudioSamplingRate(44100)
                setOutputFile(currentFilePath)
                prepare()
                start()
            }}

            isRecording = true
            updateUI()
            Toast.makeText(this, "开始录音", Toast.LENGTH_SHORT).show()

        }} catch (e: Exception) {{
            e.printStackTrace()
            Toast.makeText(this, "录音失败: ${{e.message}}", Toast.LENGTH_LONG).show()
        }}
    }}

    private fun stopRecording() {{
        try {{
            mediaRecorder?.apply {{
                stop()
                release()
            }}
            mediaRecorder = null
            isRecording = false
            updateUI()
            
            val fileName = File(currentFilePath).name
            Toast.makeText(this, "已保存: $fileName", Toast.LENGTH_LONG).show()

        }} catch (e: Exception) {{
            e.printStackTrace()
            Toast.makeText(this, "停止录音失败: ${{e.message}}", Toast.LENGTH_LONG).show()
        }}
    }}

    private fun updateUI() {{
        findViewById<android.widget.Button>(R.id.btnStartRecording).isEnabled = !isRecording
        findViewById<android.widget.Button>(R.id.btnStopRecording).isEnabled = isRecording
        
        val statusView = findViewById<android.widget.TextView>(R.id.tvStatus)
        if (isRecording) {{
            statusView.text = "正在录音..."
            statusView.setTextColor(getColor(R.color.recording))
        }} else {{
            statusView.text = "未录音"
            statusView.setTextColor(getColor(R.color.idle))
        }}
    }}

    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray
    ) {{
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == PERMISSION_REQUEST_CODE) {{
            if (grantResults.all {{ it == PackageManager.PERMISSION_GRANTED }}) {{
                Toast.makeText(this, "权限已授予", Toast.LENGTH_SHORT).show()
            }} else {{
                Toast.makeText(this, "需要录音权限才能使用", Toast.LENGTH_LONG).show()
            }}
        }}
    }}

    override fun onDestroy() {{
        super.onDestroy()
        mediaRecorder?.release()
        mediaRecorder = null
    }}
}}
''')
    print(f"✓ 已创建 MainActivity.kt")
    
    # 修改 AndroidManifest.xml
    manifest_path = os.path.join(project_dir, "app", "src", "main", "AndroidManifest.xml")
    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            content = f.read()
        content = content.replace("com.你的包名.app", app_id)
        with open(manifest_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✓ 已配置 AndroidManifest.xml")
    
    print(f"\n=== 项目创建完成！===")
    print(f"应用名称: {app_name}")
    print(f"包名: {app_id}")
    print(f"项目路径: {project_dir}")
    print(f"\n下一步: 用 Android Studio 打开 {project_dir} 文件夹")

if __name__ == "__main__":
    # ====== 在这里修改 ======
    APP_NAME = "myrecorder"  # 应用名称
    # ========================
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.join(base_dir, APP_NAME)
    
    create_project(project_dir, APP_NAME)
