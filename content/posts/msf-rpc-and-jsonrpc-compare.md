---
title: "msf的rpc和json-rpc，我该选择哪个？"
date: 2020-05-07 18:59:00
tags:
- msf
- 红队
- 工具
categories:
- 开发
---



msf的rpc有两种调用方式，那么我们应该调用哪一个呢？

<!--more-->

其中restful接口暂且不谈，这个rest api其实是简单对接了一下msf的后端数据库，这个自己也能读数据库来做，这个以后有时间再谈

首先说下这个json-rpc，json-rpc是metasploit5.0推出的一个功能，采用json作为交互格式，例如

```
akkuman@DESKTOP-MFL946C ~> curl -k -X POST -H "Accept: application/json" -H "Content-Type: application/json" -H "Authorization: Bearer f622f07405f68533c549bc11838c9f1b6b1f14ba5caae75fb726da071b73f8315aaf3b9b0186fc51" -d '{"jsonrpc": "2.0", "method": "core.version", "id": 1 }' http://192.168.174.136:8081/api/v1/json-rpc
{"jsonrpc":"2.0","result":{"version":"5.0.87-dev-2dc26db9e1","ruby":"2.6.6 x86_64-linux 2020-03-31","api":"1.0"},"id":1}
```

而以前的msf的rpc是采用msgpack作为交互格式，除了没有json方便之外还有什么其他的区别吗？

答案是没有的

我们看看源码

`lib/msf/core/rpc/json/dispatcher.rb`

```ruby
    # Process the JSON-RPC request.
    # @param source [String] the JSON-RPC request
    # @return [String] JSON-RPC response that encapsulates the RPC result
    # if successful; otherwise, a JSON-RPC error response.
    def process(source)
      begin
        request = parse_json_request(source)
        if request.is_a?(Array)
          # If the batch rpc call itself fails to be recognized as an valid
          # JSON or as an Array with at least one value, the response from
          # the Server MUST be a single Response object.
          raise InvalidRequest.new if request.empty?
          # process batch request
          response = request.map { |r| process_request(r) }
          # A Response object SHOULD exist for each Request object, except that
          # there SHOULD NOT be any Response objects for notifications.
          # Remove nil responses from response array
          response.compact!
        else
          response = process_request(request)
        end
      rescue ParseError, InvalidRequest => e
        # If there was an error in detecting the id in the Request object
        # (e.g. Parse error/Invalid Request), then the id member MUST be
        # Null. Don't pass request obj when building the error response.
        response = self.class.create_error_response(e)
      rescue RpcError => e
        # other JSON-RPC errors should include the id from the Request object
        response = self.class.create_error_response(e, request)
      rescue => e
        response = self.class.create_error_response(ApplicationServerError.new(e), request)
      end

      # When a rpc call is made, the Server MUST reply with a Response, except
      # for in the case of Notifications. The Response is expressed as a single
      # JSON Object.
      self.class.to_json(response)
    end
```

里面的响应是使用 process_request，往下跟

`lib/msf/core/rpc/json/dispatcher.rb`

```ruby
    # Validate and execute the JSON-RPC request.
    # @param request [Hash] the JSON-RPC request
    # @returns [RpcCommand] an RpcCommand for the specified version
    # @raise [InvalidParams] ArgumentError occurred during execution.
    # @raise [ApplicationServerError] General server-error wrapper around an
    # Msf::RPC::Exception that occurred during execution.
    # @returns [Hash] JSON-RPC response that encapsulates the RPC result
    # if successful; otherwise, a JSON-RPC error response.
    def process_request(request)
      begin
        if !validate_rpc_request(request)
          response = self.class.create_error_response(InvalidRequest.new)
          return response
        end

        # dispatch method execution to command
        result = @command.execute(request[:method], request[:params])

        # A Notification is a Request object without an "id" member. A Request
        # object that is a Notification signifies the Client's lack of interest
        # in the corresponding Response object, and as such no Response object
        # needs to be returned to the client. The Server MUST NOT reply to a
        # Notification, including those that are within a batch request.
        if request.key?(:id)
          response = self.class.create_success_response(result, request)
        else
          response = nil
        end

        response
      rescue ArgumentError
        raise InvalidParams.new
      rescue Msf::RPC::Exception => e
        raise ApplicationServerError.new(e.message, data: { code: e.code })
      end
    end
```

可以看到 `@command.execute`，往下跟我们会发现出现了好几个，往上看能发现

```ruby
    # Set the command.
    # @param command [RpcCommand] the command used by the Dispatcher.
    def set_command(command)
      @command = command
    end
```

说明 `@command` 是一个 `RpcCommand` 类对象，但是出现了好几个这样的类，这里我们可以通过断点或者打印 `@command` 来判断，关于怎么在msf上下断调试以后有时间再写文章

我这里是通过打印，发现是 `Msf::RPC::JSON::V1_0::RpcCommand` 类，定位到这个类的 execute 方法

`lib/msf/core/rpc/json/v1_0/rpc_command.rb`

```ruby
      # Invokes the method on the receiver object with the specified params,
      # returning the method's return value.
      # @param method [String] the RPC method name
      # @param params [Array, Hash] parameters for the RPC call
      # @returns [Object] the method's return value.
      def execute(method, params)
        result = execute_internal(method, params)
        result = post_process_result(result, method, params)

        result
      end
```

我们先看看 `post_process_result`

```ruby
...
      MODULE_EXECUTE_KEY = 'module.execute'
      PAYLOAD_MODULE_TYPE_KEY = 'payload'
      PAYLOAD_KEY = 'payload'
...
      # Perform custom post processing of the execute result data.
      # @param result [Object] the method's return value
      # @param method [String] the RPC method name
      # @param params [Array, Hash] parameters for the RPC call
      # @returns [Object] processed method's return value
      def post_process_result(result, method, params)
        # post-process payload module result for JSON output
        if method == MODULE_EXECUTE_KEY && params.size >= 2 &&
            params[0] == PAYLOAD_MODULE_TYPE_KEY && result.key?(PAYLOAD_KEY)
          result[PAYLOAD_KEY] = Base64.strict_encode64(result[PAYLOAD_KEY])
        end

        result
      end
```

可以看到这个函数的功能大致上就是假如请求的json-rpc是生成可执行文件，就base64再返回，而rpc因为使用的msgpack，所以直接返回的二进制流

然后我们看看主要的调用函数 `execute_internal`

```ruby
      # Internal method that invokes the method on the receiver object with
      # the specified params, returning the method's return value.
      # @param method [String] the RPC method name
      # @param params [Array, Hash] parameters for the RPC call
      # @raise [MethodNotFound] The method does not exist
      # @raise [Timeout::Error] The method failed to terminate in @execute_timeout seconds
      # @returns [Object] the method's return value.
      def execute_internal(method, params)
        group, base_method = parse_method_group(method)

        method_name = "rpc_#{base_method}"
        method_name_noauth = "rpc_#{base_method}_noauth"

        handler = (find_handler(@legacy_rpc_service.handlers, group, method_name) || find_handler(@legacy_rpc_service.handlers, group, method_name_noauth))
        if handler.nil?
          raise MethodNotFound.new(method)
        end

        if handler.respond_to?(method_name_noauth)
          method_name = method_name_noauth
        end

        ::Timeout.timeout(@execute_timeout) do
          params = prepare_params(params)
          if params.nil?
            return handler.send(method_name)
          elsif params.is_a?(Array)
            return handler.send(method_name, *params)
          else
            return handler.send(method_name, **params)
          end
        end
      end
```

可以看到先经过处理之后，调用了 `@legacy_rpc_service` 得到 `handler`，而这个 `legacy_rpc_service` 则又是调用了原始 rpc 了，然后调用 send 方法来调用rpc，所以json-rpc实际上就是在原始rpc上包装了一层，功能上并没有变化

## 结论

两者功能相同，用哪个看个人喜好