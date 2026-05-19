package com.getvoice.app

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
import com.getvoice.app.databinding.ActivityMainBinding
import java.io.File
import java.text.SimpleDateFormat
import java.util.*

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private var mediaRecorder: MediaRecorder? = null
    private var isRecording = false
    private var currentFilePath: String? = null

    companion object {
        private const val PERMISSION_REQUEST_CODE = 100
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        setupButtons()
        checkPermissions()
        updateFilePathDisplay()
    }

    private fun getMp3Dir(): File {
        return File(Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_MUSIC), "GetVoice")
    }

    private fun setupButtons() {
        binding.btnStartRecording.setOnClickListener {
            if (!isRecording) startRecording()
        }

        binding.btnStopRecording.setOnClickListener {
            if (isRecording) stopRecording()
        }

        binding.btnRename.setOnClickListener {
            renameFile()
        }
    }

    private fun updateFilePathDisplay() {
        val mp3Dir = getMp3Dir()
        if (!mp3Dir.exists()) mp3Dir.mkdirs()
        
        binding.tvFilePath.text = "保存路径: ${mp3Dir.absolutePath}"
    }

    private fun renameFile() {
        val newName = binding.etFileName.text.toString().trim()
        if (newName.isEmpty()) {
            Toast.makeText(this, "文件名不能为空", Toast.LENGTH_SHORT).show()
            return
        }

        if (currentFilePath == null || !File(currentFilePath).exists()) {
            Toast.makeText(this, "没有可重命名的文件", Toast.LENGTH_SHORT).show()
            return
        }

        try {
            val oldFile = File(currentFilePath)
            val newFile = File(oldFile.parent, "$newName.mp3")
            
            if (newFile.exists()) {
                Toast.makeText(this, "文件名已存在", Toast.LENGTH_SHORT).show()
                return
            }

            oldFile.renameTo(newFile)
            currentFilePath = newFile.absolutePath
            updateFilePathDisplay()
            binding.etFileName.text.clear()
            binding.btnRename.isEnabled = false
            Toast.makeText(this, "已重命名为: $newName.mp3", Toast.LENGTH_LONG).show()
        } catch (e: Exception) {
            Toast.makeText(this, "重命名失败: ${e.message}", Toast.LENGTH_LONG).show()
        }
    }

    private fun checkPermissions() {
        val permissions = mutableListOf<String>()
        
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) 
            != PackageManager.PERMISSION_GRANTED) {
            permissions.add(Manifest.permission.RECORD_AUDIO)
        }

        if (Build.VERSION.SDK_INT <= Build.VERSION_CODES.P &&
            ContextCompat.checkSelfPermission(this, Manifest.permission.WRITE_EXTERNAL_STORAGE) 
            != PackageManager.PERMISSION_GRANTED) {
            permissions.add(Manifest.permission.WRITE_EXTERNAL_STORAGE)
        }

        if (permissions.isNotEmpty()) {
            ActivityCompat.requestPermissions(this, permissions.toTypedArray(), PERMISSION_REQUEST_CODE)
        }
    }

    private fun startRecording() {
        try {
            val mp3Dir = getMp3Dir()
            if (!mp3Dir.exists()) mp3Dir.mkdirs()

            val timestamp = SimpleDateFormat("yyyyMMdd_HHmmss", Locale.getDefault()).format(Date())
            val fileName = "recording_$timestamp.mp3"
            val outputFile = File(mp3Dir, fileName)
            currentFilePath = outputFile.absolutePath

            mediaRecorder = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                MediaRecorder(this)
            } else {
                @Suppress("DEPRECATION")
                MediaRecorder()
            }

            mediaRecorder?.apply {
                setAudioSource(MediaRecorder.AudioSource.MIC)
                setOutputFormat(MediaRecorder.OutputFormat.MPEG_4)
                setAudioEncoder(MediaRecorder.AudioEncoder.AAC)
                setAudioEncodingBitRate(128000)
                setAudioSamplingRate(44100)
                setOutputFile(currentFilePath)
                prepare()
                start()
            }

            isRecording = true
            updateUI()
            binding.tvFileInfo.text = "正在录音..."
            Toast.makeText(this, "开始录音", Toast.LENGTH_SHORT).show()

        } catch (e: Exception) {
            e.printStackTrace()
            Toast.makeText(this, "录音失败: ${e.message}", Toast.LENGTH_LONG).show()
        }
    }

    private fun stopRecording() {
        try {
            mediaRecorder?.apply {
                stop()
                release()
            }
            mediaRecorder = null
            isRecording = false
            updateUI()
            
            if (currentFilePath != null) {
                val file = File(currentFilePath)
                binding.tvFileInfo.text = "录音完成"
                binding.tvFilePath.text = "文件: ${file.name}\n路径: ${file.parent}"
                binding.btnRename.isEnabled = true
            }
            
        } catch (e: Exception) {
            e.printStackTrace()
            Toast.makeText(this, "停止录音失败: ${e.message}", Toast.LENGTH_LONG).show()
        }
    }

    private fun updateUI() {
        binding.btnStartRecording.isEnabled = !isRecording
        binding.btnStopRecording.isEnabled = isRecording
        
        if (isRecording) {
            binding.tvStatus.text = "正在录音..."
            binding.tvStatus.setTextColor(getColor(R.color.recording))
        } else {
            binding.tvStatus.text = "未录音"
            binding.tvStatus.setTextColor(getColor(R.color.idle))
        }
    }

    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == PERMISSION_REQUEST_CODE) {
            if (grantResults.all { it == PackageManager.PERMISSION_GRANTED }) {
                Toast.makeText(this, "权限已授予", Toast.LENGTH_SHORT).show()
            } else {
                Toast.makeText(this, "需要录音权限才能使用", Toast.LENGTH_LONG).show()
            }
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        mediaRecorder?.release()
        mediaRecorder = null
    }
}
