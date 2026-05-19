import os
import base64


def encode_to_base8(data_bytes):
    return ''.join(format(byte, '03o') for byte in data_bytes)


def encode_to_base16(data_bytes):
    return data_bytes.hex()


def encode_to_base32(data_bytes):
    return base64.b32encode(data_bytes).decode('ascii')


def encode_to_base64(data_bytes):
    return base64.b64encode(data_bytes).decode('ascii')


def encode_data(data_bytes, algorithm):
    if "Base2" in algorithm or "二进制" in algorithm:
        return ''.join(format(byte, '08b') for byte in data_bytes)
    elif "Base8" in algorithm or "八进制" in algorithm:
        return encode_to_base8(data_bytes)
    elif "Base16" in algorithm or "十六进制" in algorithm:
        return encode_to_base16(data_bytes)
    elif "Base32" in algorithm:
        return encode_to_base32(data_bytes)
    elif "Base64" in algorithm:
        return encode_to_base64(data_bytes)
    else:
        raise ValueError(f"不支持的算法: {algorithm}")


def text_to_binary(text):
    try:
        bytes_data = text.encode('utf-8')
    except UnicodeEncodeError:
        bytes_data = text.encode('latin-1')
    return ''.join(format(byte, '08b') for byte in bytes_data)


def _ensure_directory_exists(file_path):
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)


def file_to_binary(file_path, output_path, progress_callback=None):
    preview_bits = []
    total_size = os.path.getsize(file_path)
    total_bits = total_size * 8
    processed = 0
    chunk_size = 64 * 1024

    try:
        _ensure_directory_exists(output_path)

        with open(file_path, 'rb') as fin, open(output_path, 'w', encoding='utf-8') as fout:
            while True:
                chunk = fin.read(chunk_size)
                if not chunk:
                    break

                binary_chunk = ''.join(format(byte, '08b') for byte in chunk)
                fout.write(binary_chunk)

                if len(''.join(preview_bits)) < 100:
                    remaining = 100 - len(''.join(preview_bits))
                    preview_bits.append(binary_chunk[:remaining])

                processed += len(chunk)

                if total_size > 1024 * 1024 and progress_callback:
                    progress = (processed / total_size) * 100
                    progress_callback(progress)

        return ''.join(preview_bits), total_bits

    except Exception as e:
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
            except:
                pass
        raise e


def encode_file(file_path, output_path, algorithm, progress_callback=None):
    preview_chars = []
    total_size = os.path.getsize(file_path)

    if "Base2" in algorithm or "二进制" in algorithm:
        total_chars = total_size * 8
    elif "Base8" in algorithm or "八进制" in algorithm:
        total_chars = total_size * 3
    elif "Base16" in algorithm or "十六进制" in algorithm:
        total_chars = total_size * 2
    elif "Base32" in algorithm:
        total_chars = ((total_size + 4) // 5) * 8
    elif "Base64" in algorithm:
        total_chars = ((total_size + 2) // 3) * 4
    else:
        raise ValueError(f"不支持的算法: {algorithm}")

    processed = 0
    chunk_size = 64 * 1024

    try:
        _ensure_directory_exists(output_path)

        with open(file_path, 'rb') as fin, open(output_path, 'w', encoding='utf-8') as fout:
            while True:
                chunk = fin.read(chunk_size)
                if not chunk:
                    break

                encoded_chunk = encode_data(chunk, algorithm)
                fout.write(encoded_chunk)

                if len(''.join(preview_chars)) < 100:
                    remaining = 100 - len(''.join(preview_chars))
                    preview_chars.append(encoded_chunk[:remaining])

                processed += len(chunk)

                if total_size > 1024 * 1024 and progress_callback:
                    progress = (processed / total_size) * 100
                    progress_callback(progress)

        return ''.join(preview_chars), total_chars

    except Exception as e:
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
            except:
                pass
        raise e
