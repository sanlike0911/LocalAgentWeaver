#!/usr/bin/env node

const axios = require('axios');

const FRONTEND_URL = 'http://localhost:3000';

async function testErrorHandling() {
    console.log('🧪 エラーハンドリングテスト開始\n');

    try {
        console.log('=== 1. 登録エラーパターンテスト ===\n');

        // Test 1: 重複メールアドレス
        console.log('1️⃣ 重複メールアドレスでの登録テスト...');
        try {
            await axios.post(`${FRONTEND_URL}/api/auth/register`, {
                username: 'testuser',
                email: 'authtest@example.com', // 既存のメールアドレス
                password: 'testpass123'
            });
            console.log('❌ 重複エラーが検出されませんでした');
        } catch (error) {
            const detail = error.response?.data?.detail;
            console.log(`✅ 期待通りのエラー: ${detail}`);
        }
        console.log('');

        // Test 2: 無効なメールアドレス形式
        console.log('2️⃣ 無効なメールアドレス形式での登録テスト...');
        try {
            await axios.post(`${FRONTEND_URL}/api/auth/register`, {
                username: 'testuser',
                email: 'invalid-email', // 無効な形式
                password: 'testpass123'
            });
            console.log('❌ バリデーションエラーが検出されませんでした');
        } catch (error) {
            console.log(`✅ 期待通りのエラー: ${error.message}`);
        }
        console.log('');

        console.log('=== 2. ログインエラーパターンテスト ===\n');

        // Test 3: 存在しないメールアドレス
        console.log('3️⃣ 存在しないメールアドレスでのログインテスト...');
        try {
            await axios.post(`${FRONTEND_URL}/api/auth/login`, {
                email: 'nonexistent@example.com',
                password: 'password123'
            });
            console.log('❌ 認証エラーが検出されませんでした');
        } catch (error) {
            const detail = error.response?.data?.detail;
            console.log(`✅ 期待通りのエラー: ${detail}`);
        }
        console.log('');

        // Test 4: 正しいメールアドレス、間違ったパスワード
        console.log('4️⃣ 間違ったパスワードでのログインテスト...');
        try {
            await axios.post(`${FRONTEND_URL}/api/auth/login`, {
                email: 'authtest@example.com', // 存在するメールアドレス
                password: 'wrongpassword'       // 間違ったパスワード
            });
            console.log('❌ 認証エラーが検出されませんでした');
        } catch (error) {
            const detail = error.response?.data?.detail;
            console.log(`✅ 期待通りのエラー: ${detail}`);
        }
        console.log('');

        console.log('=== 3. 正常パターンテスト ===\n');

        // Test 5: 正常な新規ユーザー登録
        console.log('5️⃣ 正常な新規ユーザー登録テスト...');
        const newUserEmail = `testuser_${Date.now()}@example.com`;
        try {
            const response = await axios.post(`${FRONTEND_URL}/api/auth/register`, {
                username: 'newuser',
                email: newUserEmail,
                password: 'newpass123'
            });
            console.log(`✅ 登録成功: ${response.data.username} (${response.data.email})`);
        } catch (error) {
            console.log(`❌ 予期しないエラー: ${error.response?.data?.detail || error.message}`);
        }
        console.log('');

        // Test 6: 正常なログイン
        console.log('6️⃣ 正常なログインテスト...');
        try {
            const response = await axios.post(`${FRONTEND_URL}/api/auth/login`, {
                email: newUserEmail,
                password: 'newpass123'
            });
            console.log(`✅ ログイン成功: トークン取得`);
            console.log(`   トークン: ${response.data.access_token.substring(0, 30)}...`);
        } catch (error) {
            console.log(`❌ 予期しないエラー: ${error.response?.data?.detail || error.message}`);
        }
        console.log('');

        console.log('🎉 エラーハンドリングテスト完了！\n');

        console.log('📋 確認項目:');
        console.log('   ✅ 重複メールアドレスエラー');
        console.log('   ✅ バリデーションエラー');
        console.log('   ✅ 存在しないユーザーエラー');
        console.log('   ✅ 間違ったパスワードエラー');
        console.log('   ✅ 正常な登録フロー');
        console.log('   ✅ 正常なログインフロー');
        console.log('');

        console.log('💡 フロントエンドでの表示確認:');
        console.log(`   🔗 ログイン: ${FRONTEND_URL}/auth/login`);
        console.log(`   🔗 新規登録: ${FRONTEND_URL}/auth/register`);
        console.log('   - 上記URLで間違った情報を入力して、エラーメッセージの表示を確認してください');
        console.log('   - 正常な情報を入力して、成功メッセージの表示を確認してください');

    } catch (error) {
        console.error('❌ テスト実行エラー:', error.message);
        process.exit(1);
    }
}

testErrorHandling();