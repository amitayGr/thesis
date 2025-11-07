"""
Performance Benchmark Script for Geometry Learning API

This script tests the performance improvements by making requests
to various endpoints and measuring response times.
"""

import requests
import time
import statistics
from typing import List, Dict

BASE_URL = "http://localhost:17654"

def measure_endpoint(url: str, method: str = "GET", data: dict = None, iterations: int = 10) -> Dict:
    """Measure response time for an endpoint over multiple iterations."""
    times = []
    
    for i in range(iterations):
        start = time.time()
        try:
            if method == "GET":
                response = requests.get(url)
            else:
                response = requests.post(url, json=data)
            
            elapsed = (time.time() - start) * 1000  # Convert to milliseconds
            times.append(elapsed)
            
            # Extract X-Response-Time header if available
            if 'X-Response-Time' in response.headers:
                server_time = response.headers['X-Response-Time']
            else:
                server_time = "N/A"
            
            if i == 0:  # First request
                print(f"  First request: {elapsed:.2f}ms (Server: {server_time})")
        
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return None
        
        # Small delay between requests
        time.sleep(0.1)
    
    return {
        'min': min(times),
        'max': max(times),
        'avg': statistics.mean(times),
        'median': statistics.median(times),
        'stdev': statistics.stdev(times) if len(times) > 1 else 0
    }


def test_cache_effectiveness(url: str):
    """Test if caching is working by comparing first vs subsequent requests."""
    print(f"\n🔍 Testing cache effectiveness: {url}")
    
    # First request (cache miss)
    start = time.time()
    response1 = requests.get(url)
    time1 = (time.time() - start) * 1000
    
    # Second request (should be cached)
    time.sleep(0.1)
    start = time.time()
    response2 = requests.get(url)
    time2 = (time.time() - start) * 1000
    
    improvement = ((time1 - time2) / time1) * 100
    
    print(f"  First request (cache miss):  {time1:.2f}ms")
    print(f"  Second request (cache hit):  {time2:.2f}ms")
    print(f"  Improvement: {improvement:.1f}% faster")
    
    if improvement > 50:
        print(f"  ✅ Cache is working effectively!")
    elif improvement > 0:
        print(f"  ⚠️  Cache shows some improvement")
    else:
        print(f"  ❌ Cache may not be working")
    
    return improvement


def test_compression(url: str):
    """Test if response compression is working."""
    print(f"\n📦 Testing compression: {url}")
    
    # Request without compression
    response_uncompressed = requests.get(url, headers={'Accept-Encoding': 'identity'})
    size_uncompressed = len(response_uncompressed.content)
    
    # Request with compression
    response_compressed = requests.get(url, headers={'Accept-Encoding': 'gzip'})
    size_compressed = len(response_compressed.content)
    
    # Check if actually compressed
    is_compressed = 'gzip' in response_compressed.headers.get('Content-Encoding', '')
    
    if is_compressed:
        reduction = ((size_uncompressed - size_compressed) / size_uncompressed) * 100
        print(f"  Uncompressed: {size_uncompressed} bytes")
        print(f"  Compressed:   {size_compressed} bytes")
        print(f"  Reduction: {reduction:.1f}%")
        print(f"  ✅ Compression is working!")
    else:
        print(f"  Size: {size_uncompressed} bytes")
        print(f"  ⚠️  Response may be too small for compression")
    
    return is_compressed


def run_benchmark():
    """Run comprehensive performance benchmark."""
    
    print("=" * 70)
    print("🚀 Geometry Learning API - Performance Benchmark")
    print("=" * 70)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running and healthy\n")
        else:
            print(f"❌ Server returned status code: {response.status_code}\n")
            return
    except Exception as e:
        print(f"❌ Cannot connect to server at {BASE_URL}")
        print(f"   Error: {e}")
        print(f"\n   Please start the server with: python api_server.py\n")
        return
    
    endpoints_to_test = [
        {
            'name': 'Health Check',
            'url': f'{BASE_URL}/api/health',
            'method': 'GET',
            'cache_test': False
        },
        {
            'name': 'Get All Theorems (Cached)',
            'url': f'{BASE_URL}/api/theorems',
            'method': 'GET',
            'cache_test': True,
            'compression_test': True
        },
        {
            'name': 'Get Triangle Types (Cached)',
            'url': f'{BASE_URL}/api/db/triangles',
            'method': 'GET',
            'cache_test': True
        },
        {
            'name': 'Get Feedback Options (Cached)',
            'url': f'{BASE_URL}/api/feedback/options',
            'method': 'GET',
            'cache_test': True
        },
    ]
    
    results = []
    
    for endpoint in endpoints_to_test:
        print(f"\n{'=' * 70}")
        print(f"📊 Testing: {endpoint['name']}")
        print(f"{'=' * 70}")
        
        stats = measure_endpoint(endpoint['url'], endpoint['method'], iterations=10)
        
        if stats:
            print(f"\n  📈 Statistics (10 iterations):")
            print(f"     Minimum:   {stats['min']:.2f}ms")
            print(f"     Maximum:   {stats['max']:.2f}ms")
            print(f"     Average:   {stats['avg']:.2f}ms")
            print(f"     Median:    {stats['median']:.2f}ms")
            print(f"     Std Dev:   {stats['stdev']:.2f}ms")
            
            results.append({
                'name': endpoint['name'],
                'stats': stats
            })
            
            # Test caching if enabled
            if endpoint.get('cache_test', False):
                improvement = test_cache_effectiveness(endpoint['url'])
            
            # Test compression if enabled
            if endpoint.get('compression_test', False):
                test_compression(endpoint['url'])
    
    # Summary
    print(f"\n{'=' * 70}")
    print("📊 PERFORMANCE SUMMARY")
    print(f"{'=' * 70}\n")
    
    print(f"{'Endpoint':<40} {'Avg Time':<12} {'Rating'}")
    print("-" * 70)
    
    for result in results:
        name = result['name'][:39]
        avg = result['stats']['avg']
        
        # Rating based on response time
        if avg < 10:
            rating = "🟢 Excellent"
        elif avg < 30:
            rating = "🟡 Good"
        elif avg < 100:
            rating = "🟠 Fair"
        else:
            rating = "🔴 Slow"
        
        print(f"{name:<40} {avg:>6.2f}ms     {rating}")
    
    overall_avg = statistics.mean([r['stats']['avg'] for r in results])
    print(f"\n{'Overall Average':<40} {overall_avg:>6.2f}ms")
    
    print("\n" + "=" * 70)
    print("✅ Benchmark complete!")
    print("=" * 70)
    
    # Performance recommendations
    print("\n💡 Performance Insights:")
    
    if overall_avg < 30:
        print("   🟢 Excellent performance! Server is well optimized.")
    elif overall_avg < 100:
        print("   🟡 Good performance. Consider further optimizations if needed.")
    else:
        print("   🔴 Performance could be improved. Check:")
        print("      - Database indexes (run optimize_database.py)")
        print("      - Connection pool size")
        print("      - Cache configuration")
    
    print("\n📝 Recommendations:")
    print("   - Cached endpoints should be <10ms on subsequent requests")
    print("   - Connection pool exhaustion warnings indicate need for larger pool")
    print("   - Monitor X-Response-Time header for server-side timing")
    print("   - Run optimize_database.py if queries are slow")


if __name__ == "__main__":
    try:
        run_benchmark()
    except KeyboardInterrupt:
        print("\n\n❌ Benchmark interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Benchmark failed with error: {e}")
        import traceback
        traceback.print_exc()
