from werkzeug.utils import secure_filename
from datetime import datetime
import os
import hashlib

class FileManager:
  def __init__(self , upload_folder):
    #allowed file extentions 
    self.allowed_extenstions = {'txt', 'pdf' , 'png' , 'jpg' , 'jpeg' , 'gif' , 'doc' , 'docx', 'zip' , 'mp4' ,'mp3'}
    # max file size allowed = 16 MB
    self.max_file_size = 16*1024*1024 
    self.upload_folder = upload_folder


#checking if the file size < 16mb
  def is_file_size_valid(self , file_size: int):
    return file_size <= self.max_file_size


#generate a unique name for a specific file 
  def generate_unique_filename(self ,user_id:int , original_filename : str):
    secure_name = secure_filename(original_filename)
    timestamp = datetime.now().timestamp()
    unique_filename = f"{user_id}_{timestamp}_{secure_name}"
    return unique_filename
  
#save encrypted file data to disk
  def save_encrypted_file(self , encrypted_data , filename):
    try:
      file_path = os.path.join(self.upload_folder , filename)
      with open(file_path , "wb") as f :
        f.write(encrypted_data)
      return file_path
    except Exception as e:
      raise Exception(f"Failed to save file: {str(e)}")

#read encrypted file data from disk   
  def read_ecrypted_file(self, filename):
    try:
      file_path = os.path.join(self.upload_folder , filename)
      if not os.path.exists(file_path):
        raise FileNotFoundError(f"file not found: {filename}")
      with open(file_path, "rb") as f :
        encrypted_data = f.read()
      return encrypted_data
    except Exception as e :
      raise Exception(f"failed to read file : {str(e)}")
    

#delete file from disk
  def delete_file(self , filename):
    try: 
      file_path = os.path.join(self.upload_folder , filename)
      if os.path.exists(file_path):
        os.remove(file_path)
        return True
      else:
        return False
    except Exception as e :
      print(f"error deleting file : {str(e)}")


#create a temporary decrypted file for download
  def creat_temp_file(self ,decrypted_data , original_filename):
    temp_filename = f"temp_{original_filename}"
    temp_path = os.path.join(self.upload_folder , temp_filename)

    with open(temp_path, "wb") as f :
      f.write(decrypted_data)

    return temp_path
  
#convert bytes to human-readable format
  def format_file_size( self , size_bytes):
    for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"
  
#get file extension from filename
  def get_file_extension(self, filename: str) -> str:
    if '.' in filename:
      return filename.rsplit('.', 1)[1].lower()
    return ''
  

  def hash_file_sha256(self, file_data: bytes) -> str:
    """
    Generate SHA-256 hash of file data.
    Most commonly used for file integrity verification.
    Returns the hash as a hexadecimal string.
    """
    return hashlib.sha256(file_data).hexdigest()

  def hash_file_md5(self, file_data: bytes) -> str:
    """
    Generate MD5 hash of file data.
    Faster than SHA-256 but less secure.
    Returns the hash as a hexadecimal string.
    """
    return hashlib.md5(file_data).hexdigest()

  def hash_file_sha512(self, file_data: bytes) -> str:
    """
    Generate SHA-512 hash of file data.
    More secure than SHA-256 but slower.
    Returns the hash as a hexadecimal string.
    """
    return hashlib.sha512(file_data).hexdigest()

  def verify_file_integrity(self, file_data: bytes, expected_hash: str, algorithm: str = 'sha256') -> bool:
    """
    Verify file integrity by comparing its hash with an expected hash.
    
    Args:
        file_data: The file data as bytes
        expected_hash: The expected hash string
        algorithm: The hashing algorithm to use ('sha256', 'md5', or 'sha512')
    
    Returns True if hashes match, False otherwise.
    """
    if algorithm == 'sha256':
        calculated_hash = self.hash_file_sha256(file_data)
    elif algorithm == 'md5':
        calculated_hash = self.hash_file_md5(file_data)
    elif algorithm == 'sha512':
        calculated_hash = self.hash_file_sha512(file_data)
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")
    
    return calculated_hash == expected_hash

    

  


   

