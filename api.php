<?php
/* =====================================================================
   경리 업무지원실 시스템 · 서버 저장 API (카페24 PHP + MySQL)
   - index.html 과 같은 폴더에 함께 업로드하세요.
   - 실제 접속정보는 config.php 에 넣습니다. (이 파일은 수정할 필요 없음)
   ===================================================================== */
header('Content-Type: application/json; charset=utf-8');
header('X-Content-Type-Options: nosniff');

if (!file_exists(__DIR__ . '/config.php')) {
  http_response_code(500);
  echo json_encode(['ok' => false, 'error' => 'config.php 파일이 없습니다. config.sample.php를 복사해 만드세요.']);
  exit;
}
require __DIR__ . '/config.php';

$action = isset($_GET['action']) ? $_GET['action'] : '';

/* 서버 존재 확인용 (비밀번호 불필요) */
if ($action === 'ping') { echo json_encode(['ok' => true]); exit; }

/* 접속 비밀번호 확인 */
$given = isset($_SERVER['HTTP_X_APP_PW']) ? $_SERVER['HTTP_X_APP_PW'] : '';
if (defined('APP_PASSWORD') && APP_PASSWORD !== '') {
  if (!hash_equals(APP_PASSWORD, (string)$given)) {
    http_response_code(401);
    echo json_encode(['ok' => false, 'error' => 'unauthorized']);
    exit;
  }
}

/* DB 연결 */
$mysqli = @new mysqli(DB_HOST, DB_USER, DB_PASS, DB_NAME);
if ($mysqli->connect_errno) {
  http_response_code(500);
  echo json_encode(['ok' => false, 'error' => 'DB 연결 실패: ' . $mysqli->connect_error]);
  exit;
}
$mysqli->set_charset('utf8mb4');
$mysqli->query("CREATE TABLE IF NOT EXISTS app_state (
  id INT PRIMARY KEY,
  payload LONGTEXT,
  updated_at DATETIME
) DEFAULT CHARSET=utf8mb4");

/* 불러오기 */
if ($action === 'load') {
  $res = $mysqli->query("SELECT payload, updated_at FROM app_state WHERE id = 1");
  $row = $res ? $res->fetch_assoc() : null;
  echo json_encode([
    'ok' => true,
    'payload' => $row ? $row['payload'] : null,
    'updated_at' => $row ? $row['updated_at'] : null
  ]);
  exit;
}

/* 저장하기 */
if ($action === 'save') {
  $raw = file_get_contents('php://input');
  $data = json_decode($raw, true);
  if (!isset($data['payload'])) {
    http_response_code(400);
    echo json_encode(['ok' => false, 'error' => 'payload 없음']);
    exit;
  }
  $payload = json_encode($data['payload'], JSON_UNESCAPED_UNICODE);
  $stmt = $mysqli->prepare(
    "INSERT INTO app_state (id, payload, updated_at) VALUES (1, ?, NOW())
     ON DUPLICATE KEY UPDATE payload = VALUES(payload), updated_at = NOW()"
  );
  $stmt->bind_param('s', $payload);
  $stmt->execute();
  echo json_encode(['ok' => true, 'updated_at' => date('Y-m-d H:i:s')]);
  exit;
}

http_response_code(404);
echo json_encode(['ok' => false, 'error' => 'unknown action']);
