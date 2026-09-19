# ============================================================
# SmartInterview — Download Remaining GitHub Test Files
# Run when GitHub raw content is accessible on your network.
# All files are standalone utilities — NONE affect the app.
# ============================================================

$dst  = "C:\Users\kondu\Downloads\Smart-Interview-main (1)\Smart-Interview-main\backend"
$base = "https://raw.githubusercontent.com/Ranith11/Smart-Interview-Platform/main/backend"

$files = @(
    @{ url="$base/e2e_api_test.py";       out="$dst\e2e_api_test.py" },
    @{ url="$base/migrate_db.py";         out="$dst\migrate_db.py" },
    @{ url="$base/make_test_files.py";    out="$dst\make_test_files.py" },
    @{ url="$base/runtime_test.py";       out="$dst\runtime_test.py" },
    @{ url="$base/test_optimization.py";  out="$dst\test_optimization.py" },
    @{ url="$base/test_perf_db.py";       out="$dst\test_perf_db.py" },
    @{ url="$base/multi_concept_test.py"; out="$dst\multi_concept_test.py" },
    @{ url="$base/setup_test_kb.py";      out="$dst\setup_test_kb.py" },
    @{ url="$base/get_all_kb_data.py";    out="$dst\get_all_kb_data.py" },
    @{ url="$base/test_syllabi/DBMS_Reference.txt";    out="$dst\test_syllabi\DBMS_Reference.txt" },
    @{ url="$base/test_syllabi/Network_Security.docx"; out="$dst\test_syllabi\Network_Security.docx" }
)

New-Item -ItemType Directory -Force "$dst\test_syllabi" | Out-Null
$ok = 0; $fail = 0
foreach ($f in $files) {
    try {
        Invoke-WebRequest -Uri $f.url -OutFile $f.out -UseBasicParsing -TimeoutSec 60
        Write-Host "  OK   $($f.url | Split-Path -Leaf)"
        $ok++
    } catch {
        Write-Host "  FAIL $($f.url | Split-Path -Leaf): $($_.Exception.Message)"
        $fail++
    }
}
Write-Host "Result: $ok OK, $fail FAILED"