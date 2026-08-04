# Generates bench/test_audio.wav from bench/ground_truth.txt via Windows SAPI TTS.
# Re-run any time the ground truth text changes.
Add-Type -AssemblyName System.Speech

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$text = Get-Content -Path (Join-Path $scriptDir "ground_truth.txt") -Raw
$outPath = Join-Path $scriptDir "test_audio.wav"

$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$format = New-Object System.Speech.AudioFormat.SpeechAudioFormatInfo(16000, [System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen, [System.Speech.AudioFormat.AudioChannel]::Mono)
$synth.SetOutputToWaveFile($outPath, $format)
$synth.Speak($text)
$synth.Dispose()

Write-Output "Wrote $outPath"
