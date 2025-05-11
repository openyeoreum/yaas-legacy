import os
import sox
import sys
import tempfile # 임시 파일 생성을 위해 추가
import shutil   # 파일 이동/교체를 위해 추가

def speed_up_wav_files_safe(folder_path, name_keyword, speed_factor=1.1):
    """
    Finds WAV files in a folder containing a specific keyword in their name
    and increases their playback speed, overwriting the original files safely
    using a temporary file.

    Args:
        folder_path (str): The path to the folder containing the WAV files.
        name_keyword (str): The keyword to search for in the filenames.
        speed_factor (float): The factor by which to increase the speed (e.g., 1.1 for 1.1x).
    """
    print(f"Starting processing in folder: {folder_path}")
    print(f"Looking for files containing '{name_keyword}' with '.wav' extension.")
    print(f"Target speed factor: {speed_factor}x")
    print("-" * 30)

    found_files = False
    processed_count = 0
    error_count = 0

    # Check if the folder exists
    if not os.path.isdir(folder_path):
        print(f"Error: Folder not found at '{folder_path}'")
        return

    try:
        # List all items in the directory
        for filename in os.listdir(folder_path):
            # Construct the full path
            file_path = os.path.join(folder_path, filename)

            # Check if it's a file, ends with .wav (case-insensitive), and contains the keyword
            if os.path.isfile(file_path) and \
               filename.lower().endswith('.wav') and \
               name_keyword in filename:

                found_files = True
                print(f"Found matching file: {filename}")
                temp_output_path = None  # 임시 파일 경로 변수 초기화

                try:
                    # --- 1. 임시 파일 생성 ---
                    # delete=False로 설정하여 파일을 직접 관리할 수 있게 함
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_f:
                        temp_output_path = tmp_f.name
                        # print(f"  Created temporary file: {temp_output_path}") # 디버깅용

                    # --- 2. 변환 적용 및 임시 파일에 저장 ---
                    tfm = sox.Transformer()
                    tfm.tempo(speed_factor)

                    print(f"  Applying {speed_factor}x speed transformation to temporary file...")
                    # 입력은 원본 파일, 출력은 임시 파일
                    tfm.build(file_path, temp_output_path)

                    # --- 3. 원본 파일을 변환된 임시 파일로 교체 ---
                    print(f"  Replacing original file with processed version...")
                    # shutil.move가 원본(file_path) 위치로 임시 파일(temp_output_path)을 이동/덮어쓰기 함
                    shutil.move(temp_output_path, file_path)

                    print(f"  Successfully processed and overwritten: {filename}")
                    processed_count += 1
                    temp_output_path = None # 이동 완료 후 임시 경로 추적 해제

                except sox.SoxError as e:
                    print(f"  Error processing {filename} with SoX: {e}")
                    error_count += 1
                except OSError as e:
                    # 파일 이동/교체 중 발생할 수 있는 오류 (권한 등)
                    print(f"  Error moving/replacing file {filename}: {e}")
                    error_count += 1
                except Exception as e:
                    print(f"  An unexpected error occurred with {filename}: {e}")
                    error_count += 1
                finally:
                    # --- 4. 임시 파일 정리 (오류 발생 시) ---
                    # 만약 shutil.move 전에 오류가 발생했거나 move 자체가 실패했다면
                    # 임시 파일이 남아있을 수 있으므로 삭제 시도
                    if temp_output_path and os.path.exists(temp_output_path):
                        try:
                            os.remove(temp_output_path)
                            print(f"  Cleaned up temporary file: {temp_output_path}")
                        except OSError as e:
                            print(f"  Warning: Could not remove temporary file {temp_output_path}: {e}")

                print("-" * 10) # 파일 처리 구분선

    except OSError as e:
        print(f"Error accessing folder '{folder_path}': {e}")
        return
    except Exception as e:
        print(f"An unexpected error occurred during directory listing: {e}")
        return

    print("-" * 30)
    if not found_files:
        print("No matching WAV files found to process.")
    else:
        print(f"Processing complete.")
        print(f"  Successfully processed: {processed_count} file(s)")
        print(f"  Errors encountered:   {error_count} file(s)")

# --- Configuration ---
target_folder = '/yaas/storage/s1_Yeoreum/s12_UserStorage/yeoreum_user/yeoreum_storage/250418_싯다르타/250418_싯다르타_audiobook/250418_싯다르타_mixed_audiobook_file/VoiceLayers'
keyword = '최도식'
speed = 1.06

# --- Important Warning ---
print("="*50)
print("WARNING:")
print("This script will modify WAV files in place using a temporary file method.")
print(f"Files containing '{keyword}' in the folder:")
print(f"'{target_folder}'")
print(f"will be overwritten with versions sped up by {speed}x.")
print("It is STRONGLY recommended to back up your files before proceeding.")
print("="*50)

# --- User Confirmation (Optional but Recommended) ---
# 백업 후 진행하려면 아래 주석을 해제하세요.
# confirm = input("Do you want to proceed? (yes/no): ").lower()
# if confirm == 'yes':
#    print("Proceeding with file modification...")
#    speed_up_wav_files_safe(target_folder, keyword, speed) # 수정된 함수 호출
# else:
#    print("Operation cancelled by user.")
#    sys.exit()

# --- Execute the function ---
# 확인 단계를 사용하지 않으면 바로 실행됩니다. 백업을 꼭 확인하세요!
print("Executing file modification (safe overwrite)...")
speed_up_wav_files_safe(target_folder, keyword, speed) # 수정된 함수 호출