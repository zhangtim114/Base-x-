import os
import base64


def ensure_directory_exists(file_path):
    """
    确保文件所在的目录存在，如果不存在则创建

    参数file_path: 文件的完整路径
    """
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)


def binary_to_bytes(binary_str):
    """
    将二进制字符串转换为字节数据
    每个字节由8位二进制表示

    参数binary_str: 二进制字符串（仅包含0和1，长度须为8的倍数）
    返回值: bytes对象
    """
    clean_binary = ''.join(binary_str.split())

    if len(clean_binary) % 8 != 0:
        raise ValueError(f"二进制数据长度({len(clean_binary)})不是8的倍数")

    byte_array = bytearray()
    for i in range(0, len(clean_binary), 8):
        byte = int(clean_binary[i:i+8], 2)
        byte_array.append(byte)

    return bytes(byte_array)


def bytes_to_file(bytes_data, output_path):
    """
    将字节数据以二进制模式写入文件

    参数bytes_data: 要写入的字节数据（bytes对象）
    参数output_path: 输出文件的完整路径
    """
    ensure_directory_exists(output_path)
    with open(output_path, 'wb') as f:
        f.write(bytes_data)


def decode_from_base8(encoded_str):
    """
    将八进制字符串还原为字节数据

    参数encoded_str: 八进制字符串（仅包含字符0-7）
    返回值: bytes对象
    """
    clean_str = encoded_str.replace(' ', '').replace('\n', '').replace('\r', '').replace('\t', '')

    if not all(c in '01234567' for c in clean_str):
        raise ValueError("输入数据包含非法字符，仅允许0-7")

    if len(clean_str) % 3 != 0:
        raise ValueError(f"八进制数据长度({len(clean_str)})不是3的倍数")

    byte_array = bytearray()
    for i in range(0, len(clean_str), 3):
        byte = int(clean_str[i:i+3], 8)
        byte_array.append(byte)

    return bytes(byte_array)


def decode_from_base16(encoded_str):
    """
    将十六进制字符串还原为字节数据

    参数encoded_str: 十六进制字符串（0-9, a-f, A-F）
    返回值: bytes对象
    """
    clean_str = encoded_str.replace(' ', '').replace('\n', '').replace('\r', '').replace('\t', '')

    try:
        return bytes.fromhex(clean_str)
    except ValueError as e:
        raise ValueError(f"非法的十六进制数据: {str(e)}")


def decode_from_base32(encoded_str):
    """
    将Base32字符串还原为字节数据
    使用标准Base32解码（RFC 4648）

    参数encoded_str: Base32字符串
    返回值: bytes对象
    """
    clean_str = encoded_str.strip()

    try:
        return base64.b32decode(clean_str)
    except Exception as e:
        raise ValueError(f"非法的Base32数据: {str(e)}")


def decode_from_base64(encoded_str):
    """
    将Base64字符串还原为字节数据
    使用标准Base64解码（RFC 4648）

    参数encoded_str: Base64字符串
    返回值: bytes对象
    """
    clean_str = encoded_str.strip()

    try:
        return base64.b64decode(clean_str)
    except Exception as e:
        raise ValueError(f"非法的Base64数据: {str(e)}")


def decode_data(encoded_str, algorithm):
    """
    通用的数据解码方法
    根据选择的算法调用对应的解码函数

    参数:
        encoded_str: 编码后的字符串
        algorithm: 算法名称（如"Base2 (二进制)", "Base8 (八进制)"等）
    返回值: 解码后的字节数据（bytes对象）
    """
    if "Base2" in algorithm or "二进制" in algorithm:
        return binary_to_bytes(encoded_str)
    elif "Base8" in algorithm or "八进制" in algorithm:
        return decode_from_base8(encoded_str)
    elif "Base16" in algorithm or "十六进制" in algorithm:
        return decode_from_base16(encoded_str)
    elif "Base32" in algorithm:
        return decode_from_base32(encoded_str)
    elif "Base64" in algorithm:
        return decode_from_base64(encoded_str)
    else:
        raise ValueError(f"不支持的算法: {algorithm}")


def streaming_decrypt_file(input_path, output_path, progress_callback=None):
    """
    流式解密文件：边读取二进制字符串边转换边写入
    专门用于二进制数据的流式解密

    参数:
        input_path: 包含二进制数据的输入文件路径
        output_path: 解密后数据的输出文件路径
        progress_callback: 可选的进度回调函数，接收参数 (progress_percent, status_text)
    返回:
        tuple: (预览文本, 总字节数)
    """
    preview_chars = []
    total_bytes = 0
    chunk_size = 8192

    buffer = ''

    try:
        ensure_directory_exists(output_path)

        with open(input_path, 'r', encoding='utf-8') as fin, \
             open(output_path, 'wb') as fout:

            fin.seek(0, 2)
            total_size = fin.tell()
            fin.seek(0)

            processed_chars = 0

            while True:
                chunk = fin.read(chunk_size)

                if not chunk:
                    break

                clean_chunk = chunk.replace(' ', '').replace('\n', '').replace('\r', '').replace('\t', '')

                buffer += clean_chunk

                while len(buffer) >= 8:
                    byte_bits = buffer[:8]
                    buffer = buffer[8:]

                    byte = int(byte_bits, 2)
                    fout.write(bytes([byte]))
                    total_bytes += 1

                processed_chars += len(chunk)

                if total_size > 1024 * 1024 and progress_callback:
                    progress = (processed_chars / total_size) * 100
                    status_text = f"解密中: {processed_chars/total_size*100:.2f}%"
                    progress_callback(progress, status_text)

        if len(buffer) > 0:
            pass

        try:
            with open(output_path, 'rb') as f:
                preview_bytes = f.read(200)
                preview_text = preview_bytes.decode('utf-8')
        except:
            preview_text = f"(二进制数据，共{total_bytes}字节)"

        return preview_text, total_bytes

    except Exception as e:
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
            except:
                pass
        raise e


def decode_file(input_path, output_path, algorithm, progress_callback=None):
    """
    流式解码文件：边读取编码数据边解码边写入
    支持多种算法的流式解码

    参数:
        input_path: 包含编码数据的输入文件路径
        output_path: 解密后数据的输出文件路径
        algorithm: 使用的算法名称
        progress_callback: 可选的进度回调函数，接收参数 (progress_percent, status_text)
    返回:
        tuple: (预览文本, 总字节数)
    """
    preview_bytes_buf = bytearray()
    total_bytes = 0
    chunk_size = 8192

    try:
        ensure_directory_exists(output_path)

        with open(input_path, 'r', encoding='utf-8') as fin, \
             open(output_path, 'wb') as fout:

            fin.seek(0, 2)
            total_size = fin.tell()
            fin.seek(0)

            processed_chars = 0

            if "Base32" in algorithm or "Base64" in algorithm:
                buffer = ''
                while True:
                    chunk = fin.read(chunk_size)
                    if not chunk:
                        break

                    clean_chunk = chunk.replace(' ', '').replace('\n', '').replace('\r', '').replace('\t', '')
                    buffer += clean_chunk

                    try:
                        if "Base32" in algorithm:
                            decoded = base64.b32decode(buffer)
                        else:
                            decoded = base64.b64decode(buffer)

                        fout.write(decoded)
                        total_bytes += len(decoded)

                        if len(preview_bytes_buf) < 200:
                            preview_bytes_buf.extend(decoded[:200 - len(preview_bytes_buf)])

                        buffer = ''
                    except Exception:
                        pass

                    processed_chars += len(chunk)

                    if total_size > 1024 * 1024 and progress_callback:
                        progress = (processed_chars / total_size) * 100
                        status_text = f"解密中: {processed_chars/total_size*100:.2f}%"
                        progress_callback(progress, status_text)
            else:
                full_content = fin.read()
                clean_content = full_content.replace(' ', '').replace('\n', '').replace('\r', '').replace('\t', '')

                decoded_bytes = decode_data(clean_content, algorithm)
                fout.write(decoded_bytes)
                total_bytes = len(decoded_bytes)

                if len(preview_bytes_buf) < 200:
                    preview_bytes_buf.extend(decoded_bytes[:200])

                processed_chars = total_size

                if progress_callback:
                    progress_callback(100, "解密完成")

        try:
            preview_text = bytes(preview_bytes_buf).decode('utf-8')
        except:
            preview_text = f"(二进制数据，共{total_bytes}字节)"

        return preview_text, total_bytes

    except Exception as e:
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
            except:
                pass
        raise e
