# This file was autogenerated by some hot garbage in the `uniffi` crate.
# Trust me, you don't want to mess with it!

# Common helper code.
#
# Ideally this would live in a separate .py file where it can be unittested etc
# in isolation, and perhaps even published as a re-useable package.
#
# However, it's important that the details of how this helper code works (e.g. the
# way that different builtin types are passed across the FFI) exactly match what's
# expected by the rust code on the other side of the interface. In practice right
# now that means coming from the exact some version of `uniffi` that was used to
# compile the rust component. The easiest way to ensure this is to bundle the Python
# helpers directly inline like we're doing here.

import os
import sys
import ctypes
import enum
import struct
import contextlib
import datetime
import typing
import platform

# Used for default argument values
DEFAULT = object()


class RustBuffer(ctypes.Structure):
    _fields_ = [
        ("capacity", ctypes.c_int32),
        ("len", ctypes.c_int32),
        ("data", ctypes.POINTER(ctypes.c_char)),
    ]

    @staticmethod
    def alloc(size):
        return rust_call(_UniFFILib.ffi_cicd_ffi_rustbuffer_alloc, size)

    @staticmethod
    def reserve(rbuf, additional):
        return rust_call(_UniFFILib.ffi_cicd_ffi_rustbuffer_reserve, rbuf, additional)

    def free(self):
        return rust_call(_UniFFILib.ffi_cicd_ffi_rustbuffer_free, self)

    def __str__(self):
        return "RustBuffer(capacity={}, len={}, data={})".format(
            self.capacity,
            self.len,
            self.data[0:self.len]
        )

    @contextlib.contextmanager
    def allocWithBuilder(*args):
        """Context-manger to allocate a buffer using a RustBufferBuilder.

        The allocated buffer will be automatically freed if an error occurs, ensuring that
        we don't accidentally leak it.
        """
        builder = RustBufferBuilder()
        try:
            yield builder
        except:
            builder.discard()
            raise

    @contextlib.contextmanager
    def consumeWithStream(self):
        """Context-manager to consume a buffer using a RustBufferStream.

        The RustBuffer will be freed once the context-manager exits, ensuring that we don't
        leak it even if an error occurs.
        """
        try:
            s = RustBufferStream.from_rust_buffer(self)
            yield s
            if s.remaining() != 0:
                raise RuntimeError("junk data left in buffer at end of consumeWithStream")
        finally:
            self.free()

    @contextlib.contextmanager
    def readWithStream(self):
        """Context-manager to read a buffer using a RustBufferStream.

        This is like consumeWithStream, but doesn't free the buffer afterwards.
        It should only be used with borrowed `RustBuffer` data.
        """
        s = RustBufferStream.from_rust_buffer(self)
        yield s
        if s.remaining() != 0:
            raise RuntimeError("junk data left in buffer at end of readWithStream")

class ForeignBytes(ctypes.Structure):
    _fields_ = [
        ("len", ctypes.c_int32),
        ("data", ctypes.POINTER(ctypes.c_char)),
    ]

    def __str__(self):
        return "ForeignBytes(len={}, data={})".format(self.len, self.data[0:self.len])


class RustBufferStream:
    """
    Helper for structured reading of bytes from a RustBuffer
    """

    def __init__(self, data, len):
        self.data = data
        self.len = len
        self.offset = 0

    @classmethod
    def from_rust_buffer(cls, buf):
        return cls(buf.data, buf.len)

    def remaining(self):
        return self.len - self.offset

    def _unpack_from(self, size, format):
        if self.offset + size > self.len:
            raise InternalError("read past end of rust buffer")
        value = struct.unpack(format, self.data[self.offset:self.offset+size])[0]
        self.offset += size
        return value

    def read(self, size):
        if self.offset + size > self.len:
            raise InternalError("read past end of rust buffer")
        data = self.data[self.offset:self.offset+size]
        self.offset += size
        return data

    def readI8(self):
        return self._unpack_from(1, ">b")

    def readU8(self):
        return self._unpack_from(1, ">B")

    def readI16(self):
        return self._unpack_from(2, ">h")

    def readU16(self):
        return self._unpack_from(2, ">H")

    def readI32(self):
        return self._unpack_from(4, ">i")

    def readU32(self):
        return self._unpack_from(4, ">I")

    def readI64(self):
        return self._unpack_from(8, ">q")

    def readU64(self):
        return self._unpack_from(8, ">Q")

    def readFloat(self):
        v = self._unpack_from(4, ">f")
        return v

    def readDouble(self):
        return self._unpack_from(8, ">d")

    def readCSizeT(self):
        return self._unpack_from(ctypes.sizeof(ctypes.c_size_t) , "@N")

class RustBufferBuilder:
    """
    Helper for structured writing of bytes into a RustBuffer.
    """

    def __init__(self):
        self.rbuf = RustBuffer.alloc(16)
        self.rbuf.len = 0

    def finalize(self):
        rbuf = self.rbuf
        self.rbuf = None
        return rbuf

    def discard(self):
        if self.rbuf is not None:
            rbuf = self.finalize()
            rbuf.free()

    @contextlib.contextmanager
    def _reserve(self, numBytes):
        if self.rbuf.len + numBytes > self.rbuf.capacity:
            self.rbuf = RustBuffer.reserve(self.rbuf, numBytes)
        yield None
        self.rbuf.len += numBytes

    def _pack_into(self, size, format, value):
        with self._reserve(size):
            # XXX TODO: I feel like I should be able to use `struct.pack_into` here but can't figure it out.
            for i, byte in enumerate(struct.pack(format, value)):
                self.rbuf.data[self.rbuf.len + i] = byte

    def write(self, value):
        with self._reserve(len(value)):
            for i, byte in enumerate(value):
                self.rbuf.data[self.rbuf.len + i] = byte

    def writeI8(self, v):
        self._pack_into(1, ">b", v)

    def writeU8(self, v):
        self._pack_into(1, ">B", v)

    def writeI16(self, v):
        self._pack_into(2, ">h", v)

    def writeU16(self, v):
        self._pack_into(2, ">H", v)

    def writeI32(self, v):
        self._pack_into(4, ">i", v)

    def writeU32(self, v):
        self._pack_into(4, ">I", v)

    def writeI64(self, v):
        self._pack_into(8, ">q", v)

    def writeU64(self, v):
        self._pack_into(8, ">Q", v)

    def writeFloat(self, v):
        self._pack_into(4, ">f", v)

    def writeDouble(self, v):
        self._pack_into(8, ">d", v)

    def writeCSizeT(self, v):
        self._pack_into(ctypes.sizeof(ctypes.c_size_t) , "@N", v)
# A handful of classes and functions to support the generated data structures.
# This would be a good candidate for isolating in its own ffi-support lib.

class InternalError(Exception):
    pass

class RustCallStatus(ctypes.Structure):
    """
    Error runtime.
    """
    _fields_ = [
        ("code", ctypes.c_int8),
        ("error_buf", RustBuffer),
    ]

    # These match the values from the uniffi::rustcalls module
    CALL_SUCCESS = 0
    CALL_ERROR = 1
    CALL_PANIC = 2

    def __str__(self):
        if self.code == RustCallStatus.CALL_SUCCESS:
            return "RustCallStatus(CALL_SUCCESS)"
        elif self.code == RustCallStatus.CALL_ERROR:
            return "RustCallStatus(CALL_ERROR)"
        elif self.code == RustCallStatus.CALL_PANIC:
            return "RustCallStatus(CALL_PANIC)"
        else:
            return "RustCallStatus(<invalid code>)"

def rust_call(fn, *args):
    # Call a rust function
    return rust_call_with_error(None, fn, *args)

def rust_call_with_error(error_ffi_converter, fn, *args):
    # Call a rust function and handle any errors
    #
    # This function is used for rust calls that return Result<> and therefore can set the CALL_ERROR status code.
    # error_ffi_converter must be set to the FfiConverter for the error class that corresponds to the result.
    call_status = RustCallStatus(code=RustCallStatus.CALL_SUCCESS, error_buf=RustBuffer(0, 0, None))

    args_with_error = args + (ctypes.byref(call_status),)
    result = fn(*args_with_error)
    uniffi_check_call_status(error_ffi_converter, call_status)
    return result

def rust_call_async(scaffolding_fn, callback_fn, *args):
    # Call the scaffolding function, passing it a callback handler for `AsyncTypes.py` and a pointer
    # to a python Future object.  The async function then awaits the Future.
    uniffi_eventloop = asyncio.get_running_loop()
    uniffi_py_future = uniffi_eventloop.create_future()
    uniffi_call_status = RustCallStatus(code=RustCallStatus.CALL_SUCCESS, error_buf=RustBuffer(0, 0, None))
    scaffolding_fn(*args,
       FfiConverterForeignExecutor._pointer_manager.new_pointer(uniffi_eventloop),
       callback_fn,
       # Note: It's tempting to skip the pointer manager and just use a `py_object` pointing to a
       # local variable like we do in Swift.  However, Python doesn't use cooperative cancellation
       # -- asyncio can cancel a task at anytime.  This means if we use a local variable, the Rust
       # callback could fire with a dangling pointer.
       UniFfiPyFuturePointerManager.new_pointer(uniffi_py_future),
       ctypes.byref(uniffi_call_status),
    )
    uniffi_check_call_status(None, uniffi_call_status)
    return uniffi_py_future

def uniffi_check_call_status(error_ffi_converter, call_status):
    if call_status.code == RustCallStatus.CALL_SUCCESS:
        pass
    elif call_status.code == RustCallStatus.CALL_ERROR:
        if error_ffi_converter is None:
            call_status.error_buf.free()
            raise InternalError("rust_call_with_error: CALL_ERROR, but error_ffi_converter is None")
        else:
            raise error_ffi_converter.lift(call_status.error_buf)
    elif call_status.code == RustCallStatus.CALL_PANIC:
        # When the rust code sees a panic, it tries to construct a RustBuffer
        # with the message.  But if that code panics, then it just sends back
        # an empty buffer.
        if call_status.error_buf.len > 0:
            msg = FfiConverterString.lift(call_status.error_buf)
        else:
            msg = "Unknown rust panic"
        raise InternalError(msg)
    else:
        raise InternalError("Invalid RustCallStatus code: {}".format(
            call_status.code))

# A function pointer for a callback as defined by UniFFI.
# Rust definition `fn(handle: u64, method: u32, args: RustBuffer, buf_ptr: *mut RustBuffer) -> int`
FOREIGN_CALLBACK_T = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_ulonglong, ctypes.c_ulong, ctypes.POINTER(ctypes.c_char), ctypes.c_int, ctypes.POINTER(RustBuffer))
class UniFfiPointerManagerCPython:
    """
    Manage giving out pointers to Python objects on CPython

    This class is used to generate opaque pointers that reference Python objects to pass to Rust.
    It assumes a CPython platform.  See UniFfiPointerManagerGeneral for the alternative.
    """

    def new_pointer(self, obj):
        """
        Get a pointer for an object as a ctypes.c_size_t instance

        Each call to new_pointer() must be balanced with exactly one call to release_pointer()

        This returns a ctypes.c_size_t.  This is always the same size as a pointer and can be
        interchanged with pointers for FFI function arguments and return values.
        """
        # IncRef the object since we're going to pass a pointer to Rust
        ctypes.pythonapi.Py_IncRef(ctypes.py_object(obj))
        # id() is the object address on CPython
        # (https://docs.python.org/3/library/functions.html#id)
        return id(obj)

    def release_pointer(self, address):
        py_obj = ctypes.cast(address, ctypes.py_object)
        obj = py_obj.value
        ctypes.pythonapi.Py_DecRef(py_obj)
        return obj

    def lookup(self, address):
        return ctypes.cast(address, ctypes.py_object).value

class UniFfiPointerManagerGeneral:
    """
    Manage giving out pointers to Python objects on non-CPython platforms

    This has the same API as UniFfiPointerManagerCPython, but doesn't assume we're running on
    CPython and is slightly slower.

    Instead of using real pointers, it maps integer values to objects and returns the keys as
    c_size_t values.
    """

    def __init__(self):
        self._map = {}
        self._lock = threading.Lock()
        self._current_handle = 0

    def new_pointer(self, obj):
        with self._lock:
            handle = self._current_handle
            self._current_handle += 1
            self._map[handle] = obj
        return handle

    def release_pointer(self, handle):
        with self._lock:
            return self._map.pop(handle)

    def lookup(self, handle):
        with self._lock:
            return self._map[handle]

# Pick an pointer manager implementation based on the platform
if platform.python_implementation() == 'CPython':
    UniFfiPointerManager = UniFfiPointerManagerCPython  # type: ignore
else:
    UniFfiPointerManager = UniFfiPointerManagerGeneral  # type: ignore
# Types conforming to `FfiConverterPrimitive` pass themselves directly over the FFI.
class FfiConverterPrimitive:
    @classmethod
    def check(cls, value):
        return value

    @classmethod
    def lift(cls, value):
        return value

    @classmethod
    def lower(cls, value):
        return cls.lowerUnchecked(cls.check(value))

    @classmethod
    def lowerUnchecked(cls, value):
        return value

    @classmethod
    def write(cls, value, buf):
        cls.writeUnchecked(cls.check(value), buf)

class FfiConverterPrimitiveInt(FfiConverterPrimitive):
    @classmethod
    def check(cls, value):
        try:
            value = value.__index__()
        except Exception:
            raise TypeError("'{}' object cannot be interpreted as an integer".format(type(value).__name__))
        if not isinstance(value, int):
            raise TypeError("__index__ returned non-int (type {})".format(type(value).__name__))
        if not cls.VALUE_MIN <= value < cls.VALUE_MAX:
            raise ValueError("{} requires {} <= value < {}".format(cls.CLASS_NAME, cls.VALUE_MIN, cls.VALUE_MAX))
        return super().check(value)

class FfiConverterPrimitiveFloat(FfiConverterPrimitive):
    @classmethod
    def check(cls, value):
        try:
            value = value.__float__()
        except Exception:
            raise TypeError("must be real number, not {}".format(type(value).__name__))
        if not isinstance(value, float):
            raise TypeError("__float__ returned non-float (type {})".format(type(value).__name__))
        return super().check(value)

# Helper class for wrapper types that will always go through a RustBuffer.
# Classes should inherit from this and implement the `read` and `write` static methods.
class FfiConverterRustBuffer:
    @classmethod
    def lift(cls, rbuf):
        with rbuf.consumeWithStream() as stream:
            return cls.read(stream)

    @classmethod
    def lower(cls, value):
        with RustBuffer.allocWithBuilder() as builder:
            cls.write(value, builder)
            return builder.finalize()

# Contains loading, initialization code,
# and the FFI Function declarations in a com.sun.jna.Library.
# Define some ctypes FFI types that we use in the library

"""
ctypes type for the foreign executor callback.  This is a built-in interface for scheduling
tasks

Args:
  executor: opaque c_size_t value representing the eventloop
  delay: delay in ms
  task: function pointer to the task callback
  task_data: void pointer to the task callback data

Normally we should call task(task_data) after the detail.
However, when task is NULL this indicates that Rust has dropped the ForeignExecutor and we should
decrease the EventLoop refcount.
"""
UNIFFI_FOREIGN_EXECUTOR_CALLBACK_T = ctypes.CFUNCTYPE(None, ctypes.c_size_t, ctypes.c_uint32, ctypes.c_void_p, ctypes.c_void_p)

"""
Function pointer for a Rust task, which a callback function that takes a opaque pointer
"""
UNIFFI_RUST_TASK = ctypes.CFUNCTYPE(None, ctypes.c_void_p)

def uniffi_future_callback_t(return_type):
    """
    Factory function to create callback function types for async functions
    """
    return ctypes.CFUNCTYPE(None, ctypes.c_size_t, return_type, RustCallStatus)

from pathlib import Path

def loadIndirect():
    """
    This is how we find and load the dynamic library provided by the component.
    For now we just look it up by name.
    """
    if sys.platform == "darwin":
        libname = "lib{}.dylib"
    elif sys.platform.startswith("win"):
        # As of python3.8, ctypes does not seem to search $PATH when loading DLLs.
        # We could use `os.add_dll_directory` to configure the search path, but
        # it doesn't feel right to mess with application-wide settings. Let's
        # assume that the `.dll` is next to the `.py` file and load by full path.
        libname = os.path.join(
            os.path.dirname(__file__),
            "{}.dll",
        )
    else:
        # Anything else must be an ELF platform - Linux, *BSD, Solaris/illumos
        libname = "lib{}.so"

    libname = libname.format("uniffi_cicd_ffi")
    path = str(Path(__file__).parent / libname)
    lib = ctypes.cdll.LoadLibrary(path)
    return lib

def uniffi_check_contract_api_version(lib):
    # Get the bindings contract version from our ComponentInterface
    bindings_contract_version = 22
    # Get the scaffolding contract version by calling the into the dylib
    scaffolding_contract_version = lib.ffi_cicd_ffi_uniffi_contract_version()
    if bindings_contract_version != scaffolding_contract_version:
        raise InternalError("UniFFI contract version mismatch: try cleaning and rebuilding your project")

def uniffi_check_api_checksums(lib):
    if lib.uniffi_cicd_ffi_checksum_method_createschema_if_not_exists() != 20354:
        raise InternalError("UniFFI API checksum mismatch: try cleaning and rebuilding your project")
    if lib.uniffi_cicd_ffi_checksum_method_createschema_schema_name() != 8679:
        raise InternalError("UniFFI API checksum mismatch: try cleaning and rebuilding your project")
    if lib.uniffi_cicd_ffi_checksum_constructor_createschema_new() != 63784:
        raise InternalError("UniFFI API checksum mismatch: try cleaning and rebuilding your project")

# A ctypes library to expose the extern-C FFI definitions.
# This is an implementation detail which will be called internally by the public API.

_UniFFILib = loadIndirect()
_UniFFILib.uniffi_cicd_ffi_fn_free_createschema.argtypes = (
    ctypes.c_void_p,
    ctypes.POINTER(RustCallStatus),
)
_UniFFILib.uniffi_cicd_ffi_fn_free_createschema.restype = None
_UniFFILib.uniffi_cicd_ffi_fn_constructor_createschema_new.argtypes = (
    ctypes.c_int8,
    RustBuffer,
    ctypes.POINTER(RustCallStatus),
)
_UniFFILib.uniffi_cicd_ffi_fn_constructor_createschema_new.restype = ctypes.c_void_p
_UniFFILib.uniffi_cicd_ffi_fn_method_createschema_if_not_exists.argtypes = (
    ctypes.c_void_p,
    ctypes.POINTER(RustCallStatus),
)
_UniFFILib.uniffi_cicd_ffi_fn_method_createschema_if_not_exists.restype = ctypes.c_int8
_UniFFILib.uniffi_cicd_ffi_fn_method_createschema_schema_name.argtypes = (
    ctypes.c_void_p,
    ctypes.POINTER(RustCallStatus),
)
_UniFFILib.uniffi_cicd_ffi_fn_method_createschema_schema_name.restype = RustBuffer
_UniFFILib.ffi_cicd_ffi_rustbuffer_alloc.argtypes = (
    ctypes.c_int32,
    ctypes.POINTER(RustCallStatus),
)
_UniFFILib.ffi_cicd_ffi_rustbuffer_alloc.restype = RustBuffer
_UniFFILib.ffi_cicd_ffi_rustbuffer_from_bytes.argtypes = (
    ForeignBytes,
    ctypes.POINTER(RustCallStatus),
)
_UniFFILib.ffi_cicd_ffi_rustbuffer_from_bytes.restype = RustBuffer
_UniFFILib.ffi_cicd_ffi_rustbuffer_free.argtypes = (
    RustBuffer,
    ctypes.POINTER(RustCallStatus),
)
_UniFFILib.ffi_cicd_ffi_rustbuffer_free.restype = None
_UniFFILib.ffi_cicd_ffi_rustbuffer_reserve.argtypes = (
    RustBuffer,
    ctypes.c_int32,
    ctypes.POINTER(RustCallStatus),
)
_UniFFILib.ffi_cicd_ffi_rustbuffer_reserve.restype = RustBuffer
_UniFFILib.uniffi_cicd_ffi_checksum_method_createschema_if_not_exists.argtypes = (
)
_UniFFILib.uniffi_cicd_ffi_checksum_method_createschema_if_not_exists.restype = ctypes.c_uint16
_UniFFILib.uniffi_cicd_ffi_checksum_method_createschema_schema_name.argtypes = (
)
_UniFFILib.uniffi_cicd_ffi_checksum_method_createschema_schema_name.restype = ctypes.c_uint16
_UniFFILib.uniffi_cicd_ffi_checksum_constructor_createschema_new.argtypes = (
)
_UniFFILib.uniffi_cicd_ffi_checksum_constructor_createschema_new.restype = ctypes.c_uint16
_UniFFILib.ffi_cicd_ffi_uniffi_contract_version.argtypes = (
)
_UniFFILib.ffi_cicd_ffi_uniffi_contract_version.restype = ctypes.c_uint32
uniffi_check_contract_api_version(_UniFFILib)
uniffi_check_api_checksums(_UniFFILib)

# Public interface members begin here.


class FfiConverterBool(FfiConverterPrimitive):
    @classmethod
    def check(cls, value):
        return not not value

    @classmethod
    def read(cls, buf):
        return cls.lift(buf.readU8())

    @classmethod
    def writeUnchecked(cls, value, buf):
        buf.writeU8(value)

    @staticmethod
    def lift(value):
        return value != 0

class FfiConverterString:
    @staticmethod
    def check(value):
        if not isinstance(value, str):
            raise TypeError("argument must be str, not {}".format(type(value).__name__))
        return value

    @staticmethod
    def read(buf):
        size = buf.readI32()
        if size < 0:
            raise InternalError("Unexpected negative string length")
        utf8Bytes = buf.read(size)
        return utf8Bytes.decode("utf-8")

    @staticmethod
    def write(value, buf):
        value = FfiConverterString.check(value)
        utf8Bytes = value.encode("utf-8")
        buf.writeI32(len(utf8Bytes))
        buf.write(utf8Bytes)

    @staticmethod
    def lift(buf):
        with buf.consumeWithStream() as stream:
            return stream.read(stream.remaining()).decode("utf-8")

    @staticmethod
    def lower(value):
        value = FfiConverterString.check(value)
        with RustBuffer.allocWithBuilder() as builder:
            builder.write(value.encode("utf-8"))
            return builder.finalize()



class CreateSchema:
    _pointer: ctypes.c_void_p
    def __init__(self, if_not_exists: "bool",schema_name: "SchemaName"):
        
        
        self._pointer = rust_call(_UniFFILib.uniffi_cicd_ffi_fn_constructor_createschema_new,
        FfiConverterBool.lower(if_not_exists),
        FfiConverterTypeSchemaName.lower(schema_name))

    def __del__(self):
        # In case of partial initialization of instances.
        pointer = getattr(self, "_pointer", None)
        if pointer is not None:
            rust_call(_UniFFILib.uniffi_cicd_ffi_fn_free_createschema, pointer)

    # Used by alternative constructors or any methods which return this type.
    @classmethod
    def _make_instance_(cls, pointer):
        # Lightly yucky way to bypass the usual __init__ logic
        # and just create a new instance with the required pointer.
        inst = cls.__new__(cls)
        inst._pointer = pointer
        return inst


    def if_not_exists(self, ) -> "bool":
        return FfiConverterBool.lift(
            rust_call(_UniFFILib.uniffi_cicd_ffi_fn_method_createschema_if_not_exists,self._pointer,)
        )






    def schema_name(self, ) -> "SchemaName":
        return FfiConverterTypeSchemaName.lift(
            rust_call(_UniFFILib.uniffi_cicd_ffi_fn_method_createschema_schema_name,self._pointer,)
        )






class FfiConverterTypeCreateSchema:
    @classmethod
    def read(cls, buf):
        ptr = buf.readU64()
        if ptr == 0:
            raise InternalError("Raw pointer value was null")
        return cls.lift(ptr)

    @classmethod
    def write(cls, value, buf):
        if not isinstance(value, CreateSchema):
            raise TypeError("Expected CreateSchema instance, {} found".format(value.__class__.__name__))
        buf.writeU64(cls.lower(value))

    @staticmethod
    def lift(value):
        return CreateSchema._make_instance_(value)

    @staticmethod
    def lower(value):
        return value._pointer





class SchemaName:
    def __init__(self):
        raise RuntimeError("SchemaName cannot be instantiated directly")

    # Each enum variant is a nested class of the enum itself.
    class NAME:
        def __init__(self,name):
            
            self.name = name
            

        def __str__(self):
            return "SchemaName.NAME(name={})".format(self.name)

        def __eq__(self, other):
            if not other.is_name():
                return False
            if self.name != other.name:
                return False
            return True
    class AUTHORIZATION:
        def __init__(self,authorization):
            
            self.authorization = authorization
            

        def __str__(self):
            return "SchemaName.AUTHORIZATION(authorization={})".format(self.authorization)

        def __eq__(self, other):
            if not other.is_authorization():
                return False
            if self.authorization != other.authorization:
                return False
            return True
    class SCHEMA_NAME_AND_AUTHORIZATION:
        def __init__(self,name, authorization):
            
            self.name = name
            self.authorization = authorization
            

        def __str__(self):
            return "SchemaName.SCHEMA_NAME_AND_AUTHORIZATION(name={}, authorization={})".format(self.name, self.authorization)

        def __eq__(self, other):
            if not other.is_schema_name_and_authorization():
                return False
            if self.name != other.name:
                return False
            if self.authorization != other.authorization:
                return False
            return True
    

    # For each variant, we have an `is_NAME` method for easily checking
    # whether an instance is that variant.
    def is_name(self) -> bool:
        return isinstance(self, SchemaName.NAME)
    def is_authorization(self) -> bool:
        return isinstance(self, SchemaName.AUTHORIZATION)
    def is_schema_name_and_authorization(self) -> bool:
        return isinstance(self, SchemaName.SCHEMA_NAME_AND_AUTHORIZATION)
    

# Now, a little trick - we make each nested variant class be a subclass of the main
# enum class, so that method calls and instance checks etc will work intuitively.
# We might be able to do this a little more neatly with a metaclass, but this'll do.
SchemaName.NAME = type("SchemaName.NAME", (SchemaName.NAME, SchemaName,), {})  # type: ignore
SchemaName.AUTHORIZATION = type("SchemaName.AUTHORIZATION", (SchemaName.AUTHORIZATION, SchemaName,), {})  # type: ignore
SchemaName.SCHEMA_NAME_AND_AUTHORIZATION = type("SchemaName.SCHEMA_NAME_AND_AUTHORIZATION", (SchemaName.SCHEMA_NAME_AND_AUTHORIZATION, SchemaName,), {})  # type: ignore




class FfiConverterTypeSchemaName(FfiConverterRustBuffer):
    @staticmethod
    def read(buf):
        variant = buf.readI32()
        if variant == 1:
            return SchemaName.NAME(
                FfiConverterString.read(buf),
            )
        if variant == 2:
            return SchemaName.AUTHORIZATION(
                FfiConverterString.read(buf),
            )
        if variant == 3:
            return SchemaName.SCHEMA_NAME_AND_AUTHORIZATION(
                FfiConverterString.read(buf),
                FfiConverterString.read(buf),
            )
        raise InternalError("Raw enum value doesn't match any cases")

    def write(value, buf):
        if value.is_name():
            buf.writeI32(1)
            FfiConverterString.write(value.name, buf)
        if value.is_authorization():
            buf.writeI32(2)
            FfiConverterString.write(value.authorization, buf)
        if value.is_schema_name_and_authorization():
            buf.writeI32(3)
            FfiConverterString.write(value.name, buf)
            FfiConverterString.write(value.authorization, buf)


__all__ = [
    "InternalError",
    "SchemaName",
    "CreateSchema",
]

