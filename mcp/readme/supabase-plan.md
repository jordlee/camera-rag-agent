{
  "project": "MCP Server Supabase Authentication Integration",
  "language": "Python",
  "estimated_time": "2-3 hours",
  "prerequisites": {
    "supabase_account": "Create project at supabase.com",
    "google_oauth": "Set up Google OAuth credentials in Google Console",
    "required_keys": [
      "SUPABASE_URL (https://jzoapfsdbcqazzfyukwm.supabase.co)",
      "SUPABASE_SECRET_KEY (sb_secret_dIq_Zm3D4l0Z_qEp34qSxQ_btuwoqqQ)",
      "PUBLISHABLE_KEY (sb_publishable_G7hHZj1XZAfyZJWJXY1aog_Md-V2iNw)",
      "SUPABASE_JWT_SIGNING_KEY (f91ac314-eb26-41de-9ede-c7c5f0a45666)",
      "LEGACY_ANON_KEY_PUBLISHABLE (eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imp6b2FwZnNkYmNxYXp6Znl1a3dtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTkxODU5NTIsImV4cCI6MjA3NDc2MTk1Mn0.utOVB2iv6f3_cGI4u5XZVePyQG1OzREcYtzloamFpBE)",
      "LEGACY_SERVICE_ROLE_SECRET (eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imp6b2FwZnNkYmNxYXp6Znl1a3dtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1OTE4NTk1MiwiZXhwIjoyMDc0NzYxOTUyfQ.HX74vv5VYlVTG2zCw2moXxYda-BlWEhr7-wEfBK-VpM)",
      "LEGACY_JWT_SECRET (uJMoaVXoSIkIXFj5/ZpqQzWIUIT2v6dVeKIQefoXtlqvndhCgLx/SGQE/tYOlzMbYXWzUY6oC+YoBU3Pj3Ds6A==)",
    ]
  },
  "implementation_steps": [
    {
      "step": 1,
      "task": "Install Required Dependencies",
      "description": "Add Supabase Python client and JWT libraries",
      "prompt_for_claude": "Add these dependencies to requirements.txt: supabase for Supabase client, python-jose[cryptography] for JWT validation, python-dotenv for environment variables, and cachetools for token caching",
      "code_location": "requirements.txt",
      "example_code": "supabase==2.0.0\npython-jose[cryptography]==3.3.0\npython-dotenv==1.0.0\ncachetools==5.3.2\naiohttp==3.9.1"
    },
    {
      "step": 2,
      "task": "Create Supabase Configuration",
      "description": "Set up environment variables and Supabase client",
      "prompt_for_claude": "Create config/supabase.py that loads Supabase environment variables, initializes the Supabase client with both anon and service keys, and exports client instances for use throughout the application",
      "code_location": "config/supabase.py",
      "implementation_details": {
        "env_vars": [
          "SUPABASE_URL",
          "SUPABASE_ANON_KEY",
          "SUPABASE_SERVICE_KEY",
          "SUPABASE_JWT_SECRET"
        ],
        "clients": {
          "anon_client": "For public operations",
          "service_client": "For admin operations in MCP server"
        }
      },
      "example_code": "from supabase import create_client\nimport os\nfrom dotenv import load_dotenv\n\nload_dotenv()\n\n# For public operations\nanon_client = create_client(\n    os.getenv('SUPABASE_URL'),\n    os.getenv('SUPABASE_ANON_KEY')\n)\n\n# For server operations\nservice_client = create_client(\n    os.getenv('SUPABASE_URL'),\n    os.getenv('SUPABASE_SERVICE_KEY')\n)"
    },
    {
      "step": 3,
      "task": "Create Supabase Auth Validator",
      "description": "Build JWT validation for Supabase tokens",
      "prompt_for_claude": "Create auth/supabase_auth.py with a SupabaseAuth class that validates JWT tokens using Supabase's JWT secret, extracts user information, and provides methods to get user details from the database",
      "code_location": "auth/supabase_auth.py",
      "key_functions": [
        "validate_token(token: str) -> Dict",
        "get_user_by_id(user_id: str) -> Dict",
        "verify_token_claims(payload: Dict) -> bool",
        "extract_user_metadata(token_payload: Dict) -> Dict"
      ],
      "validation_checks": [
        "JWT signature validation using HS256",
        "Token expiration (exp claim)",
        "Audience validation (aud = 'authenticated')",
        "Role validation (role claim)",
        "Issuer validation"
      ],
      "example_code": "from jose import jwt, JWTError\nfrom typing import Optional, Dict\nimport time\n\nclass SupabaseAuth:\n    def __init__(self, supabase_client, jwt_secret):\n        self.client = supabase_client\n        self.jwt_secret = jwt_secret\n    \n    def validate_token(self, token: str) -> Optional[Dict]:\n        if token.startswith('Bearer '):\n            token = token[7:]\n        \n        try:\n            payload = jwt.decode(\n                token,\n                self.jwt_secret,\n                algorithms=['HS256'],\n                audience='authenticated'\n            )\n            \n            # Check expiration\n            if payload.get('exp', 0) < time.time():\n                raise JWTError('Token expired')\n            \n            return payload\n        except JWTError as e:\n            raise AuthenticationError(f'Invalid token: {e}')"
    },
    {
      "step": 4,
      "task": "Create Database Schema",
      "description": "Set up tables for MCP usage tracking",
      "prompt_for_claude": "Create database/schema.sql with tables for tracking MCP usage, user sessions, and analytics. Include Row Level Security policies so users can only see their own data",
      "code_location": "database/schema.sql",
      "tables": {
        "mcp_usage": {
          "columns": [
            "id SERIAL PRIMARY KEY",
            "user_id UUID REFERENCES auth.users(id)",
            "tool TEXT NOT NULL",
            "parameters JSONB",
            "response_time_ms INTEGER",
            "success BOOLEAN DEFAULT true",
            "error TEXT",
            "created_at TIMESTAMP DEFAULT NOW()"
          ]
        },
        "user_sessions": {
          "columns": [
            "id UUID PRIMARY KEY DEFAULT gen_random_uuid()",
            "user_id UUID REFERENCES auth.users(id)",
            "started_at TIMESTAMP DEFAULT NOW()",
            "last_activity TIMESTAMP DEFAULT NOW()",
            "mcp_calls_count INTEGER DEFAULT 0"
          ]
        }
      },
      "rls_policies": [
        "Users can only view their own MCP usage",
        "Users can only view their own sessions"
      ]
    },
    {
      "step": 5,
      "task": "Create Usage Tracker",
      "description": "Track all MCP tool calls directly in Supabase",
      "prompt_for_claude": "Create tracking/usage_tracker.py that logs MCP tool calls directly to Supabase database, including user context, tool name, parameters, response time, and error tracking",
      "code_location": "tracking/usage_tracker.py",
      "features": [
        "Async database writes to not block MCP responses",
        "Batch insert for high volume",
        "Error handling with fallback to local logging",
        "Response time calculation"
      ],
      "example_code": "import asyncio\nfrom datetime import datetime\nimport json\n\nclass UsageTracker:\n    def __init__(self, supabase_client):\n        self.client = supabase_client\n        self.pending_events = []\n    \n    async def track_async(self, user_id, tool, params, response_time_ms, success=True, error=None):\n        try:\n            await self.client.table('mcp_usage').insert({\n                'user_id': user_id,\n                'tool': tool,\n                'parameters': params,\n                'response_time_ms': response_time_ms,\n                'success': success,\n                'error': error\n            }).execute()\n        except Exception as e:\n            # Fallback to local logging\n            print(f'Failed to track usage: {e}')"
    },
    {
      "step": 6,
      "task": "Integrate Auth into MCP Server",
      "description": "Add Supabase authentication to MCP request handler",
      "prompt_for_claude": "Modify the main MCP server handler to extract Bearer tokens from request metadata, validate them using SupabaseAuth, get user details from Supabase, and attach user context to all tool calls",
      "code_location": "Update main MCP server file",
      "integration_points": [
        {
          "location": "request handler initialization",
          "modification": "Initialize SupabaseAuth with service client"
        },
        {
          "location": "request processing",
          "modification": "Extract and validate token before tool execution",
          "token_extraction": "metadata.get('authorization') or headers.get('Authorization')"
        },
        {
          "location": "tool execution",
          "modification": "Pass user context to tools and track usage"
        },
        {
          "location": "error handling",
          "modification": "Return proper auth errors without exposing details"
        }
      ],
      "example_integration": "async def handle_request(self, request, context):\n    # Extract token\n    auth_header = context.metadata.get('authorization', '')\n    if not auth_header.startswith('Bearer '):\n        raise AuthError('Missing authentication')\n    \n    # Validate token\n    token = auth_header[7:]\n    user_data = self.auth.validate_token(token)\n    \n    # Track usage\n    start_time = time.time()\n    try:\n        result = await self.process_tool(request, user_data)\n        response_time = int((time.time() - start_time) * 1000)\n        await self.tracker.track_async(\n            user_data['sub'],\n            request.method,\n            request.params,\n            response_time\n        )\n        return result\n    except Exception as e:\n        # Track error\n        await self.tracker.track_async(\n            user_data['sub'],\n            request.method,\n            request.params,\n            response_time,\n            success=False,\n            error=str(e)\n        )\n        raise"
    },
    {
      "step": 7,
      "task": "Create Session Cache",
      "description": "Cache validated tokens to reduce validation overhead",
      "prompt_for_claude": "Create auth/session_cache.py using cachetools to cache validated tokens for 5 minutes, reducing the need to validate every request",
      "code_location": "auth/session_cache.py",
      "implementation": {
        "cache_type": "TTLCache",
        "ttl": 300,
        "key_strategy": "Hash token for security",
        "max_size": 1000
      },
      "example_code": "from cachetools import TTLCache\nimport hashlib\n\nclass SessionCache:\n    def __init__(self, ttl=300, maxsize=1000):\n        self.cache = TTLCache(maxsize=maxsize, ttl=ttl)\n    \n    def get_or_validate(self, token, validator):\n        # Use hash of token as cache key\n        cache_key = hashlib.sha256(token.encode()).hexdigest()\n        \n        if cache_key in self.cache:\n            return self.cache[cache_key]\n        \n        # Validate and cache\n        user_data = validator.validate_token(token)\n        self.cache[cache_key] = user_data\n        return user_data"
    },
    {
      "step": 8,
      "task": "Update Server Initialization",
      "description": "Initialize Supabase components on MCP server start",
      "prompt_for_claude": "Update the MCP server initialization to load Supabase configuration, create service client, initialize auth validator and usage tracker, and set up the session cache",
      "code_location": "Main server file (__main__ or server.py)",
      "initialization_sequence": [
        "Load .env file",
        "Validate required Supabase variables",
        "Create Supabase service client",
        "Initialize SupabaseAuth",
        "Set up SessionCache",
        "Initialize UsageTracker",
        "Start MCP server with auth middleware"
      ]
    },
    {
      "step": 9,
      "task": "Create Test Suite",
      "description": "Test authentication flow with Supabase",
      "prompt_for_claude": "Create tests/test_supabase_auth.py that tests token validation, user data extraction, usage tracking, and session caching with real Supabase tokens",
      "code_location": "tests/test_supabase_auth.py",
      "test_scenarios": [
        "Valid token - should succeed and return user data",
        "Expired token - should reject",
        "Malformed token - should reject",
        "Missing token - should return 401",
        "Cached token - should skip validation",
        "Usage tracking - should write to database"
      ]
    },
    {
      "step": 10,
      "task": "Configure Claude Desktop Integration",
      "description": "Set up MCP config for Claude with Supabase token",
      "prompt_for_claude": "Create setup/configure_claude.py script that helps users get a Supabase token (via web app or CLI), test the token, and configure their Claude Desktop to use the MCP server with authentication",
      "code_location": "setup/configure_claude.py",
      "configuration_methods": [
        {
          "method": "Environment Variable",
          "steps": [
            "User signs in via web app",
            "Copy access token",
            "Set MCP_AUTH_TOKEN env var",
            "Configure Claude to pass env var"
          ]
        },
        {
          "method": "Claude Config File",
          "location": "~/.config/claude/config.json",
          "format": {
            "mcpServers": {
              "your-mcp-server": {
                "command": "python",
                "args": ["path/to/server.py"],
                "env": {
                  "MCP_AUTH_TOKEN": "Bearer <supabase_access_token>"
                }
              }
            }
          }
        }
      ]
    }
  ],
  "environment_variables": {
    ".env": {
      "SUPABASE_URL": "https://xxxxx.supabase.co",
      "SUPABASE_ANON_KEY": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "SUPABASE_SERVICE_KEY": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "SUPABASE_JWT_SECRET": "your-jwt-secret-from-project-settings",
      "MCP_REQUIRE_AUTH": "true",
      "LOG_LEVEL": "INFO"
    }
  },
  "supabase_setup": {
    "enable_google_auth": [
      "Go to Authentication → Providers",
      "Enable Google",
      "Add Google OAuth credentials",
      "Set redirect URL to your app"
    ],
    "database_setup": [
      "Run schema.sql in SQL editor",
      "Enable Row Level Security",
      "Create RLS policies",
      "Test with SQL queries"
    ],
    "get_keys": [
      "Settings → API",
      "Copy URL",
      "Copy anon key (public)",
      "Copy service_role key (server only)",
      "Settings → Auth → JWT Secret"
    ]
  },
  "testing_plan": {
    "get_test_token": {
      "option_1": "Use your web app to sign in and copy token",
      "option_2": "Use Supabase Dashboard → Authentication → Users → Get user token",
      "option_3": "Create test script with supabase-py to sign in"
    },
    "test_sequence": [
      "Start MCP server with Supabase config",
      "Get valid token from Supabase",
      "Test successful tool call with token",
      "Verify usage logged in database",
      "Test rejection with invalid token",
      "Test session caching works"
    ]
  },
  "claude_code_prompts": [
    {
      "order": 1,
      "prompt": "I have a Python MCP server and want to add Supabase authentication. Create config/supabase.py to initialize Supabase clients and auth/supabase_auth.py to validate JWT tokens using python-jose"
    },
    {
      "order": 2,
      "prompt": "Create tracking/usage_tracker.py to log all MCP tool calls to Supabase database with user context, and auth/session_cache.py to cache validated tokens using cachetools"
    },
    {
      "order": 3,
      "prompt": "Integrate Supabase authentication into my MCP server's request handler. Extract Bearer tokens, validate them, track usage in Supabase, and handle auth errors gracefully"
    },
    {
      "order": 4,
      "prompt": "Create database/schema.sql with tables for MCP usage tracking including Row Level Security policies, and tests/test_supabase_auth.py to verify the authentication flow"
    }
  ],
  "advantages_over_alternatives": {
    "vs_auth0": [
      "No sync needed - auth and database in same place",
      "50,000 MAUs free vs 7,000",
      "Simpler architecture - one service",
      "Built-in Row Level Security",
      "Real-time subscriptions included"
    ],
    "vs_clerk": [
      "Official Python SDK available",
      "Database included",
      "More generous free tier",
      "Direct SQL access"
    ]
  },
  "production_considerations": {
    "security": [
      "Never expose service_role key to clients",
      "Use Row Level Security on all tables",
      "Rotate JWT secret periodically",
      "Enable MFA for sensitive operations"
    ],
    "performance": [
      "Cache validated tokens",
      "Use connection pooling",
      "Index user_id columns",
      "Consider read replicas for analytics"
    ],
    "monitoring": [
      "Track auth failures in separate table",
      "Monitor usage patterns",
      "Set up alerts for unusual activity",
      "Use Supabase Dashboard for monitoring"
    ]
  },
  "troubleshooting": {
    "common_issues": [
      {
        "issue": "Token validation fails",
        "solution": "Ensure JWT_SECRET matches Supabase project settings"
      },
      {
        "issue": "Database writes fail",
        "solution": "Check RLS policies allow service role to write"
      },
      {
        "issue": "Google SSO not working",
        "solution": "Verify redirect URLs match in Google Console and Supabase"
      }
    ]
  }
}