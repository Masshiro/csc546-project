# `senders.py`解读

## 初始化函数`__init__`

**核心功能**

- **UDP套接字的创建**
  - 使用`socket.AF_INET` 和 `socket.SOCK_DGRAM` 创建 UDP 套接字
  - 绑定到指定的端口，支持多次绑定（`SO_REUSEADDR`）

- **多路复用支持**
  - 使用 `select.poll()` 监听多个事件（读、写、错误）

- **自定义策略**
  - 通过注入的 `SenderStrategy` 实现发送策略，灵活应对不同需求。
- **peer_addr 初始化**
  - `peer_addr` 用于存储接收端的地址，初始为`None`

**代码详解**

- `sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)`
  - `socket.socket()` 是创建一个套接字对象的方法
  - `socket.AF_INET`
    - 表示地址族(Address Family)
    - `AF_INET`：IPv4，`AF_INET6`：IPv6
  - `socket.SOCK_DGRAM`
    - 表示套接字的类型
    - `SOCK_DGRAM` 创建一个 UDP套接字
    - `SOCK_STREAM`创建 TCP套接字
- `sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)`
  - 三个参数：`level, option, value`
  - There are socket-level options, IP-level options, TCP-level options, etc. `SO_REUSEADDR` (and `SO_REUSEPORT`) is a socket-level option, as it affects the socket object itself (when it is binding to a local IP/port pair) [link](https://stackoverflow.com/questions/72319941/what-do-socket-sol-socket-and-socket-so-reuseaddr-in-python)
  - 作用：
  - 通常，当一个套接字关闭后，操作系统会保留一段时间的状态（处于 `TIME_WAIT` 状态），以确保剩余数据能被正确传输。在此期间，如果尝试重新绑定到相同端口，会引发 `Address already in use` 错误.启用 `SO_REUSEADDR` 后，可以绕过这个限制，立即绑定到相同端口

## 数据发送`send()`

核心流程

- 从`strategy.next_packet_to_send()`获取下一个待发送的数据包
- 如果返回值不为空，这通过`sock.sendto()`发送到`peer_addr`
- `peer_addr`是通过握手过程中确定的

## 数据接收`recv()`

功能：接收接收端返回的ACK

核心流程：

- 使用`recvfrom`接收数据包，返回数据和地址
- 数据解码并交给`strategy.process_ack()`进行处理
- **ACK处理**：反馈机制的重要环节，用于调整发送策略

## 握手建立连接`handshake()`

功能：通过UDP握手建立与接收端的连接

核心流程：

- 循环接收握手请求

- 如果接收端的消息包含 "handshake" 字段且 peer_addr 为空

  - 记录接收端的地址到 `peer_addr`
  - 向接收端发送握手确认消息
  - 打印连接建立信息

- 将套接字设置为非阻塞模式（`setblocking(0)`），以支持异步操作

- `msg, addr = self.sock.recvfrom(1600)`

  - `recvfrom(buffer_size)`:

    - `buffer_size` 是接收缓冲区的大小，表示本次可以接收的最大字节数。

    - 1600 指定了缓冲区大小为 1600 字节

- `msg` 的格式由发送端决定（也就是说，在`strategies.py`中可以找到）。如果发送端发送的是合法的 JSON 格式数据，接收到的 msg 解码后就是 JSON 格式

## 主循环`run()`

功能：主循环，在指定时间内处理发送和接收逻辑

核心流程：

- 设置超时时间（1000ms）和开始时间
- 循环监听事件：
  - 如果<u>**没有**</u>事件，调用`send()`尝试发送数据
  - 如果<u>**有**</u>事件，根据事件类型进行处理：
    - **错误事件 (**ERR_FLAGS**)**: 直接退出程序
    - **读事件 (**READ_FLAGS**)**: 调用 recv() 处理接收到的数据
    - **写事件 (**WRITE_FLAGS**)**: 调用 send() 发送数据
- 对于标志，见<a href="#FLAGS">附录</a>

---

# `receiver.py`解读

## `Peer`类

功能：管理单个发送端的接收窗口，处理数据包有序接收及调整

属性：

- `window_size`：接收窗口的大小
- `seq_num`：当前接收的数据包序列号（初始化为-1）
- `window`：存储当前接收的窗口内数据包
- `high_water_mark`：已成功接收的最大序列号，用于检测新数据包


---

# WSL中无法使用mahimahi
[可能的解决方案：更换WSL内核](https://unix.stackexchange.com/questions/700620/run-wireguard-as-a-client-on-win10-with-wsl2)





# 附录

## <a id="#FLAGS">FLAGS</a>

```python
READ_FLAGS = select.POLLIN | select.POLLPRI
WRITE_FLAGS = select.POLLOUT
ERR_FLAGS = select.POLLERR | select.POLLHUP | select.POLLNVAL
READ_ERR_FLAGS = READ_FLAGS | ERR_FLAGS
ALL_FLAGS = READ_FLAGS | WRITE_FLAGS | ERR_FLAG
```

